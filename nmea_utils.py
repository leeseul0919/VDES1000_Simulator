correct_six_bit_ascii = "0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW`abcdefghijklmnopqrstuvw"
fault_six_bit_ascii = "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_ !\"#$%&`()*+,-./0123456789:;<=>?"
def Armored_payload(t):
    res = ""
    for i in t:
        i_to_int = ord(i)
        i_to_bin = bin(i_to_int)[2:].zfill(8)
        res += f"{i_to_bin}"
    res_to_6bit_ascii = ""
    for i in range(0,(len(res)//6*6),6):
        r = res[i:i+6]
        res_to_6bit_ascii = res_to_6bit_ascii + correct_six_bit_ascii[int(r,2)]
    fill_bits = 0
    if len(res) % 6 !=0:
        fill_bits = len(res) % 6
        res_to_6bit_ascii += correct_six_bit_ascii[int(res[-fill_bits:].ljust(6,"0"),2)]
    return res_to_6bit_ascii, (6-fill_bits)

def Fault_Fill_Bits(t):
    res = ""
    for i in t:
        i_to_int = ord(i)
        i_to_bin = bin(i_to_int)[2:].zfill(8)
        res += f"{i_to_bin}"
    res_to_6bit_ascii = ""
    for i in range(0,(len(res)//6*6),6):
        r = res[i:i+6]
        res_to_6bit_ascii = res_to_6bit_ascii + correct_six_bit_ascii[int(r,2)]
    fill_bits = 0
    if len(res) % 6 !=0:
        fill_bits = len(res) % 6
        res_to_6bit_ascii += correct_six_bit_ascii[int(res[-fill_bits:].ljust(6,"0"),2)]
    return res_to_6bit_ascii, (fill_bits + 1)%6

def Fault_Armored_payload(t):
    res = ""
    for i in t:
        i_to_int = ord(i)
        i_to_bin = bin(i_to_int)[2:].zfill(8)
        res += f"{i_to_bin}"
    res_to_6bit_ascii = ""
    for i in range(0,(len(res)//6*6),6):
        r = res[i:i+6]
        res_to_6bit_ascii = res_to_6bit_ascii + fault_six_bit_ascii[int(r,2)]
    fill_bits = 0
    if len(res) % 6 !=0:
        fill_bits = len(res) % 6
        res_to_6bit_ascii += fault_six_bit_ascii[int(res[-fill_bits:].ljust(6,"0"),2)]
    return res_to_6bit_ascii, (6-fill_bits)

def Fault_Armored_Fill_Bits_payload(t):
    res = ""
    for i in t:
        i_to_int = ord(i)
        i_to_bin = bin(i_to_int)[2:].zfill(8)
        res += f"{i_to_bin}"
    res_to_6bit_ascii = ""
    for i in range(0,(len(res)//6*6),6):
        r = res[i:i+6]
        res_to_6bit_ascii = res_to_6bit_ascii + fault_six_bit_ascii[int(r,2)]
    fill_bits = 0
    if len(res) % 6 !=0:
        fill_bits = len(res) % 6
        res_to_6bit_ascii += fault_six_bit_ascii[int(res[-fill_bits:].ljust(6,"0"),2)]
    return res_to_6bit_ascii, (fill_bits + 1)%6

def Fafult_Decoding_payload(t):
    res = ""
    for i in t:
        find_idx = fault_six_bit_ascii.find(i)
        rr = bin(find_idx)[2:].zfill(6)
        res = res + rr
    res_to_chr = ""
    for i in range(0,len(res),8):
        r = res[i:i+8]
        r_to_int = int(r,2)
        res_to_chr = res_to_chr + chr(r_to_int)
    return res_to_chr

def Decoding_payload(t):
    res = ""
    for i in t:
        find_idx = correct_six_bit_ascii.find(i)
        rr = bin(find_idx)[2:].zfill(6)
        res = res + rr
    res_to_chr = ""
    for i in range(0,len(res),8):
        r = res[i:i+8]
        r_to_int = int(r,2)
        res_to_chr = res_to_chr + chr(r_to_int)
    return res_to_chr

def check_CRC(s):
    check_sum = 0
    for c in s:
        check_sum ^= ord(c)
    check_sum = f"{check_sum:02X}"
    #print(s,check_sum)
    return check_sum

def Fault_check_CRC(s):
    check_sum = 0
    for c in s:
        check_sum ^= ord(c)
    check_sum ^= ord('a')
    check_sum = f"{check_sum:02X}"
    #print(s,check_sum)
    return check_sum
