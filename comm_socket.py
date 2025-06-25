import socket, threading
from sentence_handler import *
from nmea_utils import *
import time
import datetime
from sentence_handler import *
from policy_manager import *
from gui_app import *

class CommState:
    def __init__(self):
        self.send_messages = []
        self.is_TX = 0
        self.start_time = 0
        self.needed_response_type = 0
        self.needed_queue = 0
        self.needed_EAK_A = 0
        self.needed_EDO = 0
        self.received_queue = 0
        self.received_EAK_A = 0
        self.received_EDO = 0
        self.complete_send_try = 0
        self.is_auto_manual = 0
        self.current_expected_messages = []
        self.expected_messages = []
        self.is_tx_file = 0
        self.misc_receive_count = 0
        self.misc_valid_message_count = 0
        self.sentence_type = []
        self.is_fill_bits = 0

    def reset_state(self):
        #global needed_response_type, needed_queue, needed_EAK_A, needed_EDO, received_queue, received_EAK_A, received_EDO, is_TX, complete_send_try
        self.needed_response_type = 0
        self.needed_queue = 0
        self.received_queue = 0
        self.needed_EAK_A = 0
        self.received_EAK_A = 0
        self.needed_EDO = 0
        self.received_EDO = 0
        self.is_TX = 0
        self.complete_send_try = 0


class VDESComm:
    def __init__(self,policy_manager,Port = 60000,IP_addr = "10.0.0.5"):
        self.port = Port
        self.IP_addr = IP_addr
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket.bind(("",self.port))
        self.recv_thread = threading.Thread(target=self.receive_loop)
        self.send_thread = threading.Thread(target=self.send_loop)
        self.state = CommState()

        self.sentence_type_options = policy_manager.get_non_empty_responses()
        print(self.sentence_type_options)
        for i in self.sentence_type_options: self.state.sentence_type.append(i)

        self.message_queue = []
        self.policy_manager = policy_manager
        
        self.GUI_Manager = VDESGUI(self.policy_manager, self.state, self.send_message_callback, self.send_edm_callback, self.sentence_type_options)
        self.message_manager = SendMessagesList(self.policy_manager,self.state,self.GUI_Manager)
        print(f"message_manager: {self.message_manager}")
        self.receive_manager = ReceiveMessagesParsing(self.policy_manager,self.state,self.GUI_Manager)
        #self.sentence_handler = SendMessagesList(self.policy_manager,self.state,self.GUI_Manager)
        #self.misc_receive_count = 0
        self.start()
        self.GUI_Manager.run()

    def start(self):
        self.recv_thread.start()
        self.send_thread.start()

    def send_message_callback(self,sentence_type,entries,is_auto_fill_bits):
        try:
            print("send message callback")
            #global needed_response_type, needed_queue, needed_EAK_A, needed_EDO, start_time, is_TX, complete_send_try, is_tx_file , expected_messages, current_expected_messages
            self.state.current_expected_messages.clear()
            self.state.current_expected_messages = [i for i in self.state.expected_messages]
            values = [] 
            for field, entry in entries.items():    #사용자가 입력한 값들 value에 넣기기
                value = entry.get() 
                if field == "data":                 #필드 이름이 data라면 6 bit encoding해서 전달
                    value, fill_bits = Armored_payload(value)
                    if is_auto_fill_bits == 1:
                        values.append(str(value))
                        values.append(str(fill_bits))
                        break
                values.append(str(value))
            print(value)
            #values 값들을 넘겨주면 자동으로 유형에 따라 문장을 만들어 보낼 리스트에 추가
            self.message_manager.add_message("VE",sentence_type,values,self.GUI_Manager.Fault_CRC_Use.get())
            self.state.needed_response_type = 0 
            self.state.needed_queue = len(self.state.send_messages)
            self.state.needed_EAK_A = len(self.state.send_messages)
            self.state.needed_EDO = len(self.state.send_messages)
            self.state.start_time = time.time()
            self.state.is_TX = 1
        except Exception as e:
            print(f"[Error] send_message_callback: {e}")

    def send_edm_callback(self,t,mmsi):
        '''
        mmsi: mmsi_entry.get(), 
        if t == 1: text_send_btn = tk.Button(root,text="Send",command=lambda: send_message(1))
        if t == 2: file_send_btn = tk.Button(root,text="Send",command=lambda: send_message(2))
        '''
        try:
            #global needed_response_type, needed_queue, needed_EAK_A, needed_EDO, start_time, is_TX, complete_send_try, is_tx_file
            print("edm auto callback")
            message = ""
            dest_mmsi = mmsi
            is_pass = 0
            if dest_mmsi == "":
                self.GUI_Manager.update_send_display(f"\nSend >> Please enter Destination MMSI.\n")
            elif dest_mmsi.isdigit() == False:
                self.GUI_Manager.update_send_display(f"\nSend >> Destination MMSI must be an integer. Please Check.\n")
            else:
                if t==1:
                    message = self.GUI_Manager.entry.get()
                    if message == "":
                        self.GUI_Manager.update_send_display(f"\nSend >> Please enter Text.\n")
                    else: 
                        print("edm auto message send",message)
                        self.state.is_tx_file = 1
                        is_pass = 1
                elif t==2:
                    if self.GUI_Manager.filename.get() !="":
                        print("file auto message send")
                        with open(self.GUI_Manager.filename.get(),'r',encoding='utf-8') as file:
                            message = file.read()
                            print(message)
                        is_pass = 1
                        self.state.is_tx_file = 2
                    else: self.GUI_Manager.update_send_display(f"\nSend >> Select File.\n")
            if is_pass == 1:
                if message:
                    try:
                        print(message)
                        self.state.complete_send_try = 1
                        chv1 = self.GUI_Manager.CheckVar1.get()
                        chv2 = self.GUI_Manager.CheckVar2.get()
                        chv3 = self.GUI_Manager.CheckVar3.get()

                        #EDM 메시지 자동 생성
                        if self.GUI_Manager.sentence_type_variable.get() == "EDM": self.message_manager.add_edm_message("VE",dest_mmsi,message,chv1,chv2,chv3)
                        
                        self.needed_response_type = 0
                        self.needed_queue = len(self.state.send_messages)
                        self.needed_EAK_A = len(self.state.send_messages)
                        self.needed_EDO = len(self.state.send_messages)
                        self.start_time = time.time()
                        self.state.is_TX = 1
                        self.GUI_Manager.entry.delete(0,tk.END)
                    except Exception as e:
                        print(e)
        except Exception as e:
            print(f"[Error] send_message_callback: {e}")

    def receive_loop(self):
        print("start receive")
        while True:
            try:
                message, addr = self.socket.recvfrom(1024)
                ascii_string = message.decode("ASCII")

                nmea = ascii_string[1:].split("\\")[1][1:-2]
                nmea_sentence = nmea.split("*")
                tag_block = ascii_string[1:].split("\\")[0].split("*")

                if check_CRC(nmea_sentence[0]) == nmea_sentence[1] and check_CRC(tag_block[0]) == tag_block[1]:
                    self.state.misc_receive_count = self.state.misc_receive_count + 1
                    nmea_sentence_split = nmea_sentence[0].split(",")
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.GUI_Manager.update_misc_receive_display(f"\n>> {current_time}\n   {nmea}\n   structure: {nmea_sentence_split[1:]}")
                    #메시지 자동 매핑 / policies에 들어가 있는 메시지면 전부 매핑됨
                    self.receive_manager.parsing_process(nmea_sentence_split, self.port)
            except Exception as e:
                print(f"MISC Error: {e}")
            time.sleep(0.001)

    def send_loop(self):
        print("start send")
        #global send_messages, needed_response_type, needed_queue, needed_EAK_A, needed_EDO, received_queue, received_EAK_A, received_EDO, start_time, is_TX, complete_send_try
        while True:
            if self.state.is_auto_manual == 0: #Auto Completion Mode - EDM Message
                if self.state.is_TX == 1:
                    #print(len(self.state.send_messages))
                    self.GUI_Manager.text_send_btn.config(state=tk.DISABLED)  #전송 버튼 비활성화
                    self.GUI_Manager.file_send_btn.config(state=tk.DISABLED)
                    self.GUI_Manager.file_select_btn.config(state=tk.DISABLED)
                    self.GUI_Manager.clear_file_btn.config(state=tk.DISABLED)

                    if len(self.state.send_messages) != 0: #보낼게 있을 때
                        #print(self.state.send_messages)
                        if (time.time() - self.state.start_time) < 3:  #TimeOut 전까지
                            if self.state.needed_response_type == 0 and self.state.needed_queue != self.state.received_queue:    #EAK(Q)를 하나 받았을 때 EAK(Q)를 덜 받았으면
                                s = self.state.send_messages.pop(0)[0]
                                self.socket.sendto(s.encode("ascii"),(self.IP_addr,self.port))
                                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                raw_m = s[:-2].split(",")[-2]
                                if self.GUI_Manager.CheckVar3.get() == 0: self.GUI_Manager.update_send_display(f"\n>> {current_time}\n   {s[:-2]}\n   Raw Text: {Decoding_payload(raw_m)}\n")
                                else: self.GUI_Manager.update_send_display(f"\n>> {current_time}\n   {s[:-2]}\n   Raw Text: {Fafult_Decoding_payload(raw_m)}\n")
                                
                            elif self.state.needed_response_type == 2:
                                self.GUI_Manager.update_send_display(f"\n   Transmit Fail: Fail Request - Time is Invalid.\n   Receive Messages: EAK(Q) [{self.state.received_queue}/{self.state.needed_queue}].\n")    #EAK(Q) 몇개 잃어버림
                                self.state.reset_state()
                                self.message_manager.set_line_counter(len(self.state.send_messages))
                                self.state.send_messages.clear()
                            elif self.state.needed_response_type == 3:
                                self.GUI_Manager.update_send_display(f"\n   Transmit Fail: Fail Request - Invalid Message.\n   Receive Messages: EAK(Q) [{self.state.received_queue}/{self.state.needed_queue}].\n")
                                self.state.reset_state()
                                self.message_manager.set_line_counter(len(self.state.send_messages))
                                self.state.send_messages.clear()
                        else:   #TimeOut 되고나서는
                            self.GUI_Manager.update_send_display(f"\n   Transmit Fail: Fail Request - Time Out. Please Retry.\n   Receive Messages: EAK(Q) [{self.state.received_queue}/{self.state.needed_queue}].\n")    #EAK(Q) 몇개 잃어버림
                            #보낼 때 설정해두었던 모든 변수 초기화
                            self.state.reset_state()
                            self.message_manager.set_line_counter(len(self.state.send_messages))
                            self.state.send_messages.clear()
                    else:   #보낼게 없을 때
                        if self.state.needed_queue != 0:   #받아야 하는 EAK(Q) 수 초기화 전에
                            if self.state.needed_queue == self.state.received_queue:  #EAK(Q)를 다 받았으면
                                self.GUI_Manager.update_send_display(f"\n   Succefully Sending Request.\n   Receive Messages: EAK(Q) [{self.state.received_queue}/{self.state.needed_queue}].")
                                #초기화
                                self.state.needed_response_type = 0
                                self.state.needed_queue = 0
                                self.state.received_queue = 0
                                self.state.start_time = time.time()
                            else:   #EAK(Q)를 다 못 받았을 때
                                if (time.time() - self.state.start_time) < 3:  #아직 타임아웃이 안되었을 때
                                    if self.state.needed_response_type == 2:   #EAK(N)을 받으면 실패, TX 상태 종료
                                        self.GUI_Manager.update_send_display(f"\n   Transmit Fail: Fail Request - Time is Invalid.\n   Receive Messages: EAK(Q) [{self.state.received_queue}/{self.state.needed_queue}].\n")    #EAK(Q) 몇개 잃어버림
                                        self.state.reset_state()
                                    elif self.state.needed_response_type == 3:
                                        self.GUI_Manager.update_send_display(f"\n   Transmit Fail: Fail Request - Invalid Message.\n   Receive Messages: EAK(Q) [{self.state.received_queue}/{self.state.needed_queue}].\n")
                                        self.state.reset_state()
                                else:   #타임아웃이 되면
                                    self.GUI_Manager.update_send_display(f"\n   Transmit Fail: Fail Request - Time Out. Please Retry.\n   Receive Messages: EAK(Q) [{self.state.received_queue}/{self.state.needed_queue}].")
                                    self.state.reset_state()
                        else:   #EAK(Q)를 다 받았을 때 초기화 후
                            if (time.time() - self.state.start_time) < (self.state.needed_EAK_A + 15):    #타임아웃 전
                                if self.state.needed_EAK_A == self.state.received_EAK_A and self.state.needed_EDO == self.state.received_EDO:   #모든 EAK(A)와 EDO를 받았다면
                                    self.GUI_Manager.update_send_display(f"\n   Succefully Every Transfer.\n   Receive Messages: EAK(A) [{self.state.received_EAK_A}/{self.state.needed_EAK_A}], EDO[{self.state.received_EDO}/{self.state.needed_EDO}].")
                                    self.state.reset_state()
                                elif self.state.needed_response_type == 2 and (self.state.needed_EAK_A != self.state.received_EAK_A or self.state.needed_EDO != self.state.received_EDO):  #EAK(N)을 받았다면
                                    self.GUI_Manager.update_send_display(f"\n   Transmit Fail: No Normal Responses Received.\n   Receive Messages: EAK(A) [{self.state.received_EAK_A}/{self.state.needed_EAK_A}], EDO[{self.state.received_EAK_A}/{self.state.needed_EAK_A}].\n")
                                    self.state.reset_state()
                            else:
                                if self.state.needed_EAK_A != self.state.received_EAK_A or self.state.needed_EDO != self.state.received_EDO:    #타임아웃되면
                                    self.GUI_Manager.update_send_display(f"\n   Transmit Fail: Time Out. Please Retry.\n   Receive Messages: EAK(A) [{self.state.received_EAK_A}/{self.state.needed_EAK_A}], EDO[{self.state.received_EAK_A}/{self.state.needed_EAK_A}].\n")
                                self.state.reset_state()
                else: 
                    if self.state.complete_send_try == 0:
                        print(self.state.complete_send_try)
                        if self.state.is_auto_manual == 0: 
                            if self.state.is_tx_file != 2: self.GUI_Manager.text_send_btn.config(state=tk.NORMAL)
                            self.GUI_Manager.file_send_btn.config(state=tk.NORMAL)
                            self.GUI_Manager.file_select_btn.config(state=tk.NORMAL)
                            self.GUI_Manager.clear_file_btn.config(state=tk.NORMAL)
                        self.state.complete_send_try = 1
                    self.state.start_time = time.time()  #TX 상태가 아닐 때
            else:   #Manual Completion Mode - Single Sequence Sentence for All Sentence Types
                if self.state.is_TX == 1:  #비동기 전송 시작 상태일 때
                    if len(self.state.send_messages) != 0:
                        s = self.state.send_messages.pop(0)[0]
                        self.socket.sendto(s.encode("ascii"),(self.IP_addr,self.port))
                        self.state.start_time = time.time()
                        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.GUI_Manager.update_send_display(f"\n>> {current_time}\n   {s[:-2]}")
                    else:
                        if time.time()-self.state.start_time < 3:
                            if self.state.needed_response_type == 2:
                                self.GUI_Manager.update_send_display(f"   Transmit Fail - Time is Invalid.\n   Not Receive: {self.state.current_expected_messages}")
                                self.state.is_TX = 0
                            elif self.state.needed_response_type == 3:
                                self.GUI_Manager.update_send_display(f"   Transmit Fail - Invalid Message.\n   Not Receive: {self.state.current_expected_messages}")
                                self.state.is_TX = 0
                            else:
                                if len(self.state.current_expected_messages) == 0:
                                    self.GUI_Manager.update_send_display(f"   Transmit Success.\n")
                                    self.state.is_TX = 0
                        else:
                            self.GUI_Manager.update_send_display(f"   Transmit Fail - Time Out.\n   Not Receive: {self.state.current_expected_messages}")
                            self.state.is_TX = 0
                else: self.state.start_time = time.time()
            time.sleep(0.01)