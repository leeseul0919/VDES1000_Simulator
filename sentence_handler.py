from nmea_utils import *
from gui_app import *

class SendMessagesList: #policy_manager.get_policy(), 태그 블록(tx_count, talker), utils
    def __init__(self,policy_manager,comm_state, gui_manager):
        self.policy_manager = policy_manager
        self.pending_ack = None
        self.TX_Count = 0
        self.talker = "tt00"
        self.GUI_Manager = gui_manager
        self.state = comm_state

    def set_line_counter(self,num):
        self.TX_Count -= num

    def Tag_Block_generator(self):  #NMEA Content 앞에 태그 블록 생성
        #송신 개수와 어플리케이션 토커 아이디
        tag_block_content = f"n:{self.TX_Count},s:{self.talker},d:"
        
        #이 블록의 CRC 값 계산
        tag_block_CRC = check_CRC(tag_block_content)
        tag_block = "\\" + tag_block_content + f"*{tag_block_CRC}"
        self.TX_Count += 1
        return tag_block
    
    def format_sentence(self,prefix,sentence_type,values,ch1):
        #해당 문장 유형의 표준 규칙 들고오기
        policy = self.policy_manager.get_policy(sentence_type)
        structure = policy["structure"] #구조 들고와서
        if len(values) != len(structure):   #필드 개수 확인하고
            raise ValueError(f"Invalid number of values for {sentence_type}.")
        sentence_content = ",".join(values) #,로 value 값들 연결

        #해당 문장 유형의 NMEA 센텐스 생성
        base_sentence = f"{prefix}{sentence_type},{sentence_content}"
        crc = check_CRC(base_sentence)  #CRC 값 계산
        if ch1==1: crc=Fault_check_CRC(base_sentence)
        return f"\\!{base_sentence}*{crc}\r\n"
    
    def add_message(self,prefix,sentence_type,values,ch1):
        tag_block = self.Tag_Block_generator()
        message = self.format_sentence(prefix,sentence_type,values,ch1)
        policy = self.policy_manager.get_policy(sentence_type)
        self.state.send_messages.append((tag_block+message,policy["expected_responses"],policy["requires_ack"]))
        print(self.state.send_messages)

    def add_edm_message(self,prefix,dest_mmsi,text,ch1,ch2,ch3,max_length=430):
        total_sentence_num = len(text)//max_length
        for i in range(total_sentence_num):
            divided_message = text[max_length*i:max_length*(i+1)]
            encoding_payload, fill_bits_num = Armored_payload(divided_message)
            if ch2 == 1 and ch3 == 0:
                encoding_payload, fill_bits_num = Fault_Fill_Bits(divided_message)
            elif ch2 == 0 and ch3 == 1:
                encoding_payload, fill_bits_num = Fault_Armored_payload(divided_message)
            elif ch2 == 1 and ch3 == 1:
                encoding_payload, fill_bits_num = Fault_Armored_Fill_Bits_payload(divided_message)
            values = [str(i),"",str(dest_mmsi),encoding_payload,str(fill_bits_num)]
            self.add_message(prefix,"EDM",values,ch1) 
        
        divided_message = text[max_length*total_sentence_num:]
        encoding_payload, fill_bits_num = Armored_payload(divided_message)
        if ch2 == 1 and ch3 == 0:
            encoding_payload, fill_bits_num = Fault_Fill_Bits(divided_message)
        elif ch2 == 0 and ch3 == 1:
            encoding_payload, fill_bits_num = Fault_Armored_payload(divided_message)
        elif ch2 == 1 and ch3 == 1:
            encoding_payload, fill_bits_num = Fault_Armored_Fill_Bits_payload(divided_message)
        values = [str(total_sentence_num),"",str(dest_mmsi),encoding_payload,str(fill_bits_num)]
        self.add_message(prefix,"EDM",values,ch1)

class ReceiveMessagesParsing:
    def __init__(self,policy_manager,comm_state, gui_manager):
        self.policy_manager = policy_manager
        self.comm_state = comm_state
        self.GUI_Manager = gui_manager

    def parsing_process(self, sentence_split, port=60000):
        #global needed_response_type, received_EAK_A, received_queue, received_EDO, current_expected_messages
        msg_type = sentence_split[0][2:]                    #센텐스 유형 추출
        policy = self.policy_manager.get_policy(msg_type)   #유형에 해당하는 Policy 가져오기

        structure = policy["structure"]                     #구조 가져오기
        field_conditions = policy["Field_conditions"]       #필드 조건들 가져오기
        standard_v = policy["standard_v"]                   #참고한 표준 문서 가져오기

        sentence_info = {}
        display_t = f"   {standard_v}: [{msg_type}] 모든 필드 조건 만족\n"
        for key in structure:   #각 구조의 필드들을 가져와서
            idx = structure.index(key)  # structure 리스트에서 인덱스를 가져옴
            s_split_param = sentence_split[idx+1]

            expected_type = field_conditions[key]["type"] #조건: 데이터 타입
            expected_range = field_conditions[key]["range"] #조건: 값의 범위/길이 범위
            expected_is_null = field_conditions[key]["is_null"] #조건: null 허용 여부
            
            #null이 불가능한데 null인지 검사
            if expected_is_null == False and (s_split_param == "" or s_split_param == None):
                self.GUI_Manager.update_misc_receive_display(f"   {standard_v}: [{msg_type}] [{idx+1}]번째 값은 NULL이 될 수 없음\n")
                self.comm_state.needed_response_type = 3
                raise ValueError(f"필드 {key}는 NULL이 될 수 없음")
            
            #num일 때 -> 현재 값이 int로 변환 가능한지 검사 -> 변환되었다면 값의 범위 검사
            if expected_type == "int":
                try:
                    type_check = int(s_split_param)
                except ValueError:
                    self.GUI_Manager.update_misc_receive_display(f"   {standard_v}: [{msg_type}] [{idx+1}]번째 값은 정수여야 함\n")
                    self.comm_state.needed_response_type = 3
                    raise TypeError(f"필드 {key}는 정수여야 함")
                if not (expected_range[0] <= type_check and expected_range[1] >= type_check):
                    self.GUI_Manager.update_misc_receive_display(f"   {standard_v}: [{msg_type}] [{idx+1}]번째 값이 적절하지 않음\n")
                    self.comm_state.needed_response_type = 3
                    raise ValueError(f"필드 {key} 값이 적절하지 않음")
            
            #string일 때 -> string이 맞는지 검사 -> string 길이가 범위 안에 오는지 검사
            elif expected_type == "str":
                if not isinstance(s_split_param,str):
                    self.GUI_Manager.update_misc_receive_display(f"   {standard_v}: [{msg_type}] [{idx+1}]번째 값은 문자열이어야 함\n")
                    self.comm_state.needed_response_type = 3
                    raise TypeError(f"필드 {key}는 문자열이어야 함")
                if not (expected_range[0] <= len(s_split_param) and expected_range[1] >= len(s_split_param)):
                    self.GUI_Manager.update_misc_receive_display(f"   {standard_v}: [{msg_type}] [{idx+1}]번째 값의 길이가 적절하지 않음\n")
                    self.comm_state.needed_response_type = 3
                    raise ValueError(f"필드 {key}의 길이가 적절하지 않음")            
            
            sentence_info[key] = s_split_param

            if key == "data":   #구조 필드 이름이 data라면 디코딩해보기
                edo_t = f"   Before Armored: {Decoding_payload(s_split_param)}\n"
                display_t = edo_t + display_t

        if self.comm_state.is_auto_manual == 0:
            if msg_type == "EAK":
                if sentence_split[3] == "Q":
                    self.comm_state.needed_response_type = 0
                    self.comm_state.received_queue += 1
                elif sentence_split[3] == "N":
                    self.comm_state.needed_response_type = 2
                elif sentence_split[3] == "A":
                    self.comm_state.received_EAK_A += 1
            elif msg_type == "EDO":
                self.comm_state.received_EDO += 1
            elif msg_type == "NAK":
                self.comm_state.needed_response_type = 3
        else:
            print(msg_type)
            #잘못된 문장을 송신했을 때 오는 메시지 유형
            if msg_type == "NAK":
                self.comm_state.needed_response_type = 3
            
            #시간 동기화 전 이거나 전송 요청 타임아웃 시 오는 메시지 유형
            elif msg_type == "EAK" and sentence_split[3] == "N":
                self.comm_state.needed_response_type = 2
            
            else:   #나머지 중에 -> 현재 응답받아야 할 메시지 유형 리스트에 있으면
                if msg_type in self.comm_state.current_expected_messages: 
                    #해당 항목 지우기
                    self.comm_state.current_expected_messages.remove(msg_type)
        print(self.comm_state.needed_response_type)
        self.GUI_Manager.update_misc_receive_display(display_t)
