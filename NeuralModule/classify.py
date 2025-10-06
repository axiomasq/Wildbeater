import glob
from pathlib import Path
import shutil
import ultralytics
import torch
from tqdm import tqdm

def main(
    model_path: Path,
    input_dir: Path,
    out_dir: Path,
    batch_size: int = 50,
    device: str | None = None,
    pattern: str = "*.jpg",
    copy_files: bool = False,
    verbose: bool = False,
):
    if device is None or device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ultralytics.YOLO(model_path)

    files = glob.glob(str(Path(input_dir) / pattern))
    total_files = len(files)

    out_dir.mkdir(parents=True, exist_ok=True)

    with tqdm(total=total_files, desc="Classifying images", unit="img") as pbar:
        for i in range(0, total_files, batch_size):
            batch = files[i: i + batch_size]
            
            predict = model(batch, device=device, verbose=verbose)

            for result in predict:
                label_probabilites: torch.Tensor = result.probs.data
                best_label: str = result.names[int(label_probabilites.argmax())]
                label_folder = out_dir / best_label
                label_folder.mkdir(parents=True, exist_ok=True)
                if copy_files:
                    shutil.copy(result.path, label_folder)
                else:
                    shutil.move(result.path, label_folder)
                pbar.update(1)

if __name__ == "__main__":
    try:
        main(
            model_path=Path("wildbeater/models/yolov11sbest-cls.pt"),
            input_dir=Path("RawData"),
            out_dir=Path("classify_out"),
            batch_size=50,
            device="auto",
            pattern="*.jpg",
            copy_files=False,
            verbose=False,
        )
    except KeyboardInterrupt:
        print("Terminated by user")
