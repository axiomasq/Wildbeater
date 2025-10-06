import argparse
import asyncio
from pathlib import Path
import sys


def cmd_parse(args: argparse.Namespace) -> int:
    from ParserModule import parse as parse_module
    asyncio.run(
        parse_module.run(
            query=args.query,
            pages=args.pages,
            out_dir=Path(args.out_dir),
            timeout=args.timeout,
            skip_existing=(not args.no_skip_existing),
        )
    )
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    from NeuralModule import classify as classify_module
    # Resolve model path: if not provided, load packaged model file
    if args.model:
        model_path = Path(args.model)
        classify_module.main(
            model_path=model_path,
            input_dir=Path(args.input_dir),
            out_dir=Path(args.out_dir),
            batch_size=args.batch_size,
            device=args.device,
            pattern=args.pattern,
            copy_files=bool(args.copy),
            verbose=bool(args.verbose),
        )
        return 0

    # Default packaged model
    try:
        from importlib.resources import as_file, files
        resource = files("wildbeater").joinpath("models/yolov11sbest-cls.pt")
        with as_file(resource) as model_file:
            classify_module.main(
                model_path=Path(model_file),
                input_dir=Path(args.input_dir),
                out_dir=Path(args.out_dir),
                batch_size=args.batch_size,
                device=args.device,
                pattern=args.pattern,
                copy_files=bool(args.copy),
                verbose=bool(args.verbose),
            )
            return 0
    except Exception:
        # Fallback to filesystem path next to this file
        fallback = Path(__file__).parent / "models" / "yolov11sbest-cls.pt"
        classify_module.main(
            model_path=fallback,
            input_dir=Path(args.input_dir),
            out_dir=Path(args.out_dir),
            batch_size=args.batch_size,
            device=args.device,
            pattern=args.pattern,
            copy_files=bool(args.copy),
            verbose=bool(args.verbose),
        )
        return 0


def cmd_extract_purple(args: argparse.Namespace) -> int:
    from UtilityModule.sortByColour import PurpleDetector
    input_dir = Path(args.input_dir)
    pattern = args.pattern
    
    if args.action in ("copy", "move") and args.out_dir is None:
        print("--out-dir is required when action is copy or move", file=sys.stderr)
        return 2
    
    out_dir = Path(args.out_dir) if args.out_dir else None
    
    import glob as _glob
    import shutil as _shutil

    paths = _glob.glob(str(input_dir / pattern))
    selected = []
    for p in paths:
        has_purple, purple_ratio, contours = PurpleDetector.detect_purple_regions(
            p, hsv_threshold=args.hsv_threshold, min_purple_area=args.min_area
        )
        if has_purple:
            selected.append(p)

    if args.action == "list":
        for p in selected:
            print(p)
        return 0

    assert out_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in selected:
        if args.action == "copy":
            _shutil.copy(p, out_dir)
        else:
            _shutil.move(p, out_dir)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wildbeater", 
                                     description="Wildbeater CLI",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # parse
    p_parse = subparsers.add_parser("parse", help="Parse WB and download images", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p_parse.add_argument("-q", "--query", required=True, type=str, help="Search query")
    p_parse.add_argument("-p", "--pages", type=int, default=5, help="Pages to scan")
    p_parse.add_argument("-o", "--out-dir", type=str, default="RawData", help="Output directory for images")
    p_parse.add_argument("--timeout", type=float, default=None, help="HTTP timeout in seconds")
    p_parse.add_argument("--no-skip-existing", action="store_true", help="Do not skip existing files")
    p_parse.set_defaults(func=lambda a: cmd_parse(_normalize_parse_args(a)))

    # classify
    p_cls = subparsers.add_parser("classify", help="Classify images with YOLO and sort into folders", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p_cls.add_argument("-m", "--model", type=str, default=None, help="Path to model (.pt). Defaults to packaged model if omitted")
    p_cls.add_argument("-i", "--input-dir", type=str, default="RawData")
    p_cls.add_argument("-o", "--out-dir", type=str, default="classify_out")
    p_cls.add_argument("-b", "--batch-size", type=int, default=50)
    p_cls.add_argument("-d", "--device", type=str, choices=["auto", "cpu", "cuda"], default="auto")
    p_cls.add_argument("--pattern", type=str, default="*.jpg")
    move_copy = p_cls.add_mutually_exclusive_group()
    move_copy.add_argument("--move", action="store_true", help="Move files (default)")
    move_copy.add_argument("--copy", action="store_true", help="Copy files instead of moving")
    p_cls.add_argument("--verbose", action="store_true")
    p_cls.set_defaults(func=cmd_classify)

    # extract-purple
    p_ep = subparsers.add_parser("extract-purple", help="Extract images with purple regions", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p_ep.add_argument("-i", "--input-dir", type=str, default="RawData")
    p_ep.add_argument("-o", "--out-dir", type=str, default=None)
    p_ep.add_argument("--pattern", type=str, default="*.jpg")
    p_ep.add_argument("--hsv-threshold", type=float, default=0.1)
    p_ep.add_argument("--min-area", type=int, default=100)
    p_ep.add_argument("--action", type=str, choices=["copy", "move", "list"], default="copy")
    p_ep.set_defaults(func=cmd_extract_purple)

    return parser


def _normalize_parse_args(a: argparse.Namespace) -> argparse.Namespace:
    a.skip_existing = not a.no_skip_existing
    return a


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by Ctrl+C", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

