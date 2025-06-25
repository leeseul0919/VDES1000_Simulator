from comm_socket import *
from gui_app import *
from nmea_utils import * 
from policy_manager import *

if __name__ == '__main__':

    initial_root = tk.Tk()
    initial_root.title("파일 불러오기")
    initial_root.geometry("480x480")
    policy_file_path = None

    def on_file_selected():
        global policy_file_path
        policy_file_path = tk.filedialog.askopenfilename(filetypes=[("select json", "*.json")])
        if policy_file_path and os.path.exists(policy_file_path):
            initial_root.destroy()

    load_button = tk.Button(initial_root, text="파일 불러오기", command=on_file_selected)
    load_button.pack(padx=20, pady=20)

    initial_root.mainloop()
    print(policy_file_path)

    policy_manager = SentencePolicyManager(policy_file_path)
    comm = VDESComm(policy_manager)
    #gui = VDESGUI(policy_manager)

    #comm.start()
    #gui.run()
