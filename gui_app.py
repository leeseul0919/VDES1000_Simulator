# gui_app.py

import tkinter as tk
from tkinter import ttk, filedialog
import time
from nmea_utils import Armored_payload
import os
# 필요한 모듈들 import

class VDESGUI:
    def __init__(self, policy_manager, comm_state, send_callback, edm_callback, sentence_type_options):
        self.policy_manager = policy_manager
        self.state = comm_state
        self.send_callback = send_callback  # Send 메시지 처리용 콜백
        self.edm_callback = edm_callback    # EDM 전송용 콜백
        self.sentence_type_options = sentence_type_options

        self.root = tk.Tk()
        self.root.title("VDES1000 Receiver & Transfer")
        self.root.geometry("1680x980")

        # 변수 초기화
        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self.update_buttons)
        self.filename = tk.StringVar()
        self.filename.trace_add("write", self.update_buttons)
        
        self.misc_receive_text = tk.Text(self.root,height=50,width=80,state="disabled")
        self.misc_receive_text.grid(row=2,column=0,padx=10,pady=10)
        self.misc_receive_label = tk.Label(self.root,text = "MISC")
        self.misc_receive_label.grid(row=3,column=0)

        self.send_text = tk.Text(self.root,height=50,width=70,state="disabled")
        self.send_text.grid(row=2,column=1,padx=10,pady=10)

        self.input_text_frame = tk.Frame(self.root)
        self.input_text_frame.grid(row=4, column=1)
        self.input_text_label = tk.Label(self.input_text_frame, text="Input Text:")
        self.input_text_label.pack(side="left")

        self.mmsi_frame = tk.Frame(self.root)
        self.mmsi_frame.grid(row=3,column=1,pady=10)
        self.mmsi_label = tk.Label(self.mmsi_frame,text="Dest MMSI:")
        self.mmsi_label.pack(side="left")
        self.mmsi_entry = tk.Entry(self.mmsi_frame,width=60)
        self.mmsi_entry.pack(side="left")
        self.entry = tk.Entry(self.input_text_frame, width=60, textvariable=self.entry_var)
        self.entry.pack(side="left")

        self.file_select_frame = tk.Frame(self.root)
        self.file_select_frame.grid(row=5, column=1, sticky="W", padx=12)
        self.file_select_label = tk.Label(self.file_select_frame, text="Select File")
        self.file_select_label.pack(side="left")
        self.file_select_btn = tk.Button(self.file_select_frame, command=self.open_file, text="Load\nFile")
        self.file_select_btn.pack(side="left", padx=5, pady=5)
        self.file_path_text = tk.Text(self.file_select_frame, height=3, width=55)
        self.file_path_text.pack(pady=20)
        self.file_path_text.config(state=tk.DISABLED)

        self.frame = tk.Frame(self.root)
        self.frame.grid(row=6,column=1)
        self.CheckVar1 = tk.IntVar()
        self.CheckVar2 = tk.IntVar()
        self.CheckVar3 = tk.IntVar()
        self.c1 = tk.Checkbutton(self.frame,text="Fault CRC",variable=self.CheckVar1)
        self.c2 = tk.Checkbutton(self.frame,text="Fault Fill Bits",variable=self.CheckVar2)
        self.c3 = tk.Checkbutton(self.frame,text="Fault Armored",variable=self.CheckVar3)
        self.c1.pack(side="left")
        self.c2.pack(side="left")
        self.c3.pack(side="left")

        self.entry_frame = tk.Frame(self.root)
        self.entry_frame.grid(row=2,column=4)
        self.disable_last_entry_var = tk.IntVar(value=0)
        
        self.is_auto_fill_bits = 0
        self.Fault_CRC_Use = tk.IntVar(value=0)
        #self.disable_last_entry_var = tk.IntVar(value=0)
        
        self.mode_select_frame = tk.Frame(self.root)
        self.mode_select_frame.grid(row=0, column=1,pady=5)

        self.Auto_Completion = tk.IntVar()
        self.Manual_Completion = tk.IntVar()
        self.mode = tk.StringVar(value="Auto")
        self.Auto_btn = tk.Radiobutton(self.mode_select_frame, text="NMEA Auto Completion", variable=self.mode, value="Auto",command=lambda: self.update_label())
        self.Manual_btn = tk.Radiobutton(self.mode_select_frame, text="NMEA Manual Completion", variable=self.mode, value="Manual",command=lambda: self.update_label())
        self.Auto_btn.pack(side="left", pady=5)
        self.Manual_btn.pack(pady=5)

        self.mode_description_label = tk.Label(self.root, text="")
        self.mode_description_label.grid(row=1,column=1)

        self.text_send_btn = tk.Button(self.root,text="Send",command=lambda: self.edm_callback(1,self.mmsi_entry.get()))
        self.text_send_btn.grid(row=4,column=3,pady=5)
        self.file_send_btn = tk.Button(self.root,text="Send",command=lambda: self.edm_callback(2,self.mmsi_entry.get()))
        self.file_send_btn.grid(row=5,column=3,pady=5)

        self.clear_file_btn = tk.Button(self.root, text="Clear File", command=self.clear_file)
        self.clear_file_btn.grid(row=6, column=3)

        self.sentence_type_variable = tk.StringVar()
        self.sentence_type_variable.set(self.state.sentence_type[0])
        self.sentence_select = ttk.Combobox(self.mode_select_frame, textvariable=self.sentence_type_variable, values=self.state.sentence_type)
        self.sentence_select.pack()
        self.sentence_select.bind("<<ComboboxSelected>>", lambda event: self.update_entries())

        self.entries = {}
        self.structure = []

        # 상태용 frame 등 구성
        #self.set_widgets_state(self.frame, state)
        self.update_entries()
        self.update_label()

    def update_buttons(self,*args):
        #global is_tx_file
        if self.entry_var.get() == "" and self.filename.get() == "":
            #print("Both Empty")
            self.entry.config(state=tk.NORMAL)
            self.text_send_btn.config(state=tk.NORMAL)
            self.file_send_btn.config(state=tk.NORMAL)
            self.file_select_btn.config(state=tk.NORMAL)
            self.clear_file_btn.config(state=tk.NORMAL)
            self.state.is_tx_file = 0
        elif self.entry_var.get() == "" and self.filename.get() != "":
            #print("Entry Empty")
            self.entry.config(state=tk.DISABLED)
            self.text_send_btn.config(state=tk.DISABLED)
            self.file_send_btn.config(state=tk.NORMAL)
            self.file_select_btn.config(state=tk.NORMAL)
            self.clear_file_btn.config(state=tk.NORMAL)
            self.state.is_tx_file = 1
        elif self.entry_var.get() != "" and self.filename.get() == "":
            #print("File Empty")
            self.entry.config(state=tk.NORMAL)
            self.text_send_btn.config(state=tk.NORMAL)
            self.file_send_btn.config(state=tk.DISABLED)
            self.file_select_btn.config(state=tk.DISABLED)
            self.clear_file_btn.config(state=tk.DISABLED)
            self.state.is_tx_file = 2
        else:
            self.file_send_btn.config(state=tk.DISABLED)
            self.file_select_btn.config(state=tk.DISABLED)
            self.clear_file_btn.config(state=tk.DISABLED)
            self.entry.config(state=tk.DISABLED)
            self.text_send_btn.config(state=tk.DISABLED)
            self.state.is_tx_file = 3
    
    def update_entries(self):
        #global disable_last_entry_var, entries, structure, is_fill_bits, Fault_CRC_Use, is_auto_manual, expected_messages
        selected_sentence_type = self.sentence_type_variable.get()
        self.structure = self.sentence_type_options[selected_sentence_type]["structure"]
        
        self.state.expected_messages.clear()
        for i in self.sentence_type_options[selected_sentence_type]["requires_ack"]: self.state.expected_messages.append(i)
        for i in self.sentence_type_options[selected_sentence_type]["expected_responses"]: self.state.expected_messages.append(i)
        
        for widget in self.entry_frame.winfo_children():
            widget.destroy()
        
        entry_sentence_type = tk.Label(self.entry_frame, text="< Manual Test (Single Sequence Sentence) >", pady=10)
        entry_sentence_type.pack()
        
        is_fill_bits = 0
        self.entries = {}
        for field in self.structure:
            entry_label = tk.Label(self.entry_frame, text=field)
            entry_label.pack()
            entry = tk.Entry(self.entry_frame, width=60)
            entry.pack()
            self.entries[field] = entry
            if field == "fill_bits": is_fill_bits = 1
        
        if is_fill_bits == 1:
            disable_last_entry_cb = tk.Checkbutton(self.entry_frame, text="Auto Fill Bits", variable=self.disable_last_entry_var, command=self.toggle_last_entry)
            disable_last_entry_cb.pack()
        
        Fault_CRC_Use_cb = tk.Checkbutton(self.entry_frame, text="Fault CRC", variable=self.Fault_CRC_Use)
        Fault_CRC_Use_cb.pack()
        
        manual_send_btn = tk.Button(self.entry_frame, text="Send", command=lambda: self.send_callback(selected_sentence_type, self.entries, self.disable_last_entry_var.get()))
        manual_send_btn.pack()

        if selected_sentence_type == "EDM":
            self.Auto_btn.config(state=tk.NORMAL)
        else:
            self.Auto_btn.config(state=tk.DISABLED)
            self.mode.set("Manual")
            self.update_label()
        if self.state.is_auto_manual == 0: self.manual_mode_widget_disabled()
        if self.disable_last_entry_var.get() == 1 and is_fill_bits == 1: self.entries[self.structure[-1]].config(state=tk.DISABLED)
        print(self.state.expected_messages)

    def update_label(self):
        #global is_auto_manual
        selected_mode = self.mode.get()
        self.update_buttons()
        if selected_mode == "Auto":
            self.mode_description_label.config(text="Just enter the Destination MMSI and (Text or Txt File).")
            self.auto_mode_widget_normal()
            self.manual_mode_widget_disabled()
            self.state.is_auto_manual = 0
        elif selected_mode == "Manual":
            self.mode_description_label.config(text="You can fill in all fields as you want.")
            self.auto_mode_widget_disabled()
            self.manual_mode_widget_normal()
            if self.state.is_fill_bits == 1 and self.disable_last_entry_var.get() == 1: self.toggle_last_entry()
            self.state.is_auto_manual = 1
        print(self.state.is_auto_manual)

    def open_file(self):
        file_path = tk.filedialog.askopenfilename(filetypes=[("txt files", "*.txt")])
        if file_path:
            self.filename.set(file_path)
            self.text_send_btn.config(state=tk.DISABLED)
            self.file_path_text.config(state=tk.NORMAL)
            self.file_path_text.delete(1.0, tk.END)
            self.file_path_text.insert(tk.END, file_path)
            self.file_path_text.config(state=tk.DISABLED)

    def clear_file(self):
        self.filename.set("")
        self.file_path_text.config(state=tk.NORMAL)
        self.file_path_text.delete(1.0, tk.END)
        self.file_path_text.config(state=tk.DISABLED)

    def set_widgets_state(self,frame, state):
        for child in frame.winfo_children():
            if isinstance(child, tk.Entry) or isinstance(child, tk.Button) or isinstance(child, tk.Checkbutton):
                child.config(state=state)

    def toggle_last_entry(self):
        if self.state.is_auto_manual == 1 and self.disable_last_entry_var.get() == 0:
            self.entries[self.structure[-1]].config(state=tk.NORMAL)
        elif self.state.is_auto_manual == 1 and self.disable_last_entry_var.get() == 1:
            self.entries[self.structure[-1]].config(state=tk.DISABLED)
        elif self.state.is_auto_manual == 0:
            self.entries[self.structure[-1]].config(state=tk.DISABLED)

    def update_misc_receive_display(self,text):
        self.misc_receive_text.config(state="normal")
        self.misc_receive_text.insert(tk.END,text+"\n")
        self.misc_receive_text.see(tk.END)
        self.misc_receive_text.config(state="disabled")

    def update_send_display(self,text):
        self.send_text.config(state="normal")
        self.send_text.insert(tk.END,text+"\n")
        self.send_text.see(tk.END)
        self.send_text.config(state="disabled")

    def disable_buttons(self):
        # 전송 중 disable
        self.text_send_btn.config(state=tk.DISABLED)
        self.file_send_btn.config(state=tk.DISABLED)
        self.file_select_btn.config(state=tk.DISABLED)
        self.clear_file_btn.config(state=tk.DISABLED)

    def enable_buttons(self):
        # 전송 가능 상태
        self.text_send_btn.config(state=tk.NORMAL)
        self.file_send_btn.config(state=tk.NORMAL)
        self.file_select_btn.config(state=tk.NORMAL)
        self.clear_file_btn.config(state=tk.NORMAL)

    def auto_mode_widget_disabled(self):
        self.set_widgets_state(self.mmsi_frame, 'disabled')
        self.set_widgets_state(self.frame, 'disabled')
        if self.state.is_tx_file == 2:
            self.text_send_btn.config(state="disabled")
            self.set_widgets_state(self.input_text_frame, 'disabled')
        elif self.state.is_tx_file == 1:
            self.file_send_btn.config(state="disabled")
            self.clear_file_btn.config(state="disabled")
            self.set_widgets_state(self.file_select_frame, 'disabled')
        else:
            self.file_send_btn.config(state="disabled")
            self.clear_file_btn.config(state="disabled")
            self.set_widgets_state(self.file_select_frame, 'disabled')
            self.text_send_btn.config(state="disabled")
            self.set_widgets_state(self.input_text_frame, 'disabled')

    def auto_mode_widget_normal(self):
        self.set_widgets_state(self.mmsi_frame, 'normal')
        self.set_widgets_state(self.frame, 'normal')
        if self.state.is_tx_file == 2: 
            self.text_send_btn.config(state="normal")
            self.set_widgets_state(self.input_text_frame, 'normal')
        elif self.state.is_tx_file == 1:
            self.file_send_btn.config(state="normal")
            self.clear_file_btn.config(state="normal")
            self.set_widgets_state(self.file_select_frame, 'normal')
        else:
            self.file_send_btn.config(state="normal")
            self.clear_file_btn.config(state="normal")
            self.set_widgets_state(self.file_select_frame, 'normal')
            self.text_send_btn.config(state="normal")
            self.set_widgets_state(self.input_text_frame, 'normal')

    def manual_mode_widget_disabled(self):
        self.set_widgets_state(self.entry_frame, 'disabled')

    def manual_mode_widget_normal(self):
        self.set_widgets_state(self.entry_frame, 'normal')

    def run(self):
        self.root.mainloop()
