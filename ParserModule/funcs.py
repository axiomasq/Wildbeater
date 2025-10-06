import math

def vol_host_v2(vol_id: int) -> str: 
    if 0 <= vol_id <= 143: t = "01" 
    elif 144 <= vol_id <= 287: t = "02"
    elif 288 <= vol_id <= 431: t = "03"
    elif 432 <= vol_id <= 719: t = "04" 
    elif 720 <= vol_id <= 1007: t = "05" 
    elif 1008 <= vol_id <= 1061: t = "06" 
    elif 1062 <= vol_id <= 1115: t = "07" 
    elif 1116 <= vol_id <= 1169: t = "08" 
    elif 1170 <= vol_id <= 1313: t = "09"
    elif 1314 <= vol_id <= 1601: t = "10"
    elif 1602 <= vol_id <= 1655: t = "11" 
    elif 1656 <= vol_id <= 1919: t = "12" 
    elif 1920 <= vol_id <= 2045: t = "13"
    elif 2046 <= vol_id <= 2189: t = "14" 
    elif 2190 <= vol_id <= 2405: t = "15" 
    elif 2406 <= vol_id <= 2621: t = "16" 
    elif 2622 <= vol_id <= 2837: t = "17" 
    elif 2838 <= vol_id <= 3053: t = "18" 
    elif 3054 <= vol_id <= 3269: t = "19" 
    elif 3270 <= vol_id <= 3485: t = "20" 
    elif 3486 <= vol_id <= 3701: t = "21" 
    elif 3702 <= vol_id <= 3917: t = "22" 
    elif 3918 <= vol_id <= 4133: t = "23" 
    elif 4134 <= vol_id <= 4349: t = "24" 
    elif 4350 <= vol_id <= 4565: t = "25" 
    elif 4566 <= vol_id <= 4877: t = "26" 
    elif 4878 <= vol_id <= 5189: t = "27" 
    elif 5190 <= vol_id <= 5501: t = "28" 
    elif 5502 <= vol_id <= 5813: t = "29" 
    elif 5814 <= vol_id <= 6125: t = "30" 
    elif 6126 <= vol_id <= 6437: t = "31" 
    else: t = "32" 
    
    return f"https://basket-{t}.wbbasket.ru"

def vol_feedback_host(r: int) -> str:
    if 0 <= r <= 431: n = "01"
    elif r <= 863: n = "02"
    elif r <= 1199: n = "03"
    elif r <= 1535: n = "04"
    elif r <= 1919: n = "05"
    elif r <= 2303: n = "06"
    elif r <= 2687: n = "07"
    elif r <= 3071: n = "08"
    elif r <= 3455: n = "09"
    elif r <= 3839: n = "10"
    else: n = "11"
    return f"https://feedback{n}.wbbasket.ru"

def numToUint8Array(imtid:int):
    t = [0]*8
    for n in range(8):
        t[n] = imtid % 256
        imtid = imtid // 256
    return t

def crc16Arc(imtid: int):
    t = numToUint8Array(imtid)
    n = 0
    for r in t:
        n ^= r
        for _ in range(8):
            if (1 & n) > 0:
                n = (n >> 1) ^ 40961
            else:
                n >>= 1
    return n
    
def preparefeedbackListUrl(imtid:int):
    tmp= "https://feedbacks{0}.wb.ru/feedbacks/v1/{1}".format(2 if crc16Arc(imtid)%100>=50 else 1, imtid)
    return tmp

def construct_host_v2(id_, t=0):
    vol = math.floor(id_ / 100000)
    part = math.floor(id_/ 1000)
    if t == 0: o = f"{vol_host_v2(vol)}/vol{vol}/part{part}/{id_}/info/ru/card.json"
    elif t == 2: o = f"{vol_feedback_host(vol)}/vol{vol}/part{part}/{id_}/photos/fs.jpg"
    elif t ==1: o = preparefeedbackListUrl(id_)
    else:
        o=""
        
    return o

if __name__=="__main__":
    print(construct_host_v2(124170265, 1))