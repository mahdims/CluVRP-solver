import tkinter as tk
from tkinter import filedialog, Text
import os
homedir = os.environ['HOME']

root = tk.Tk()
root.title("Routing Tool")
Input_file = None

# Create the frames
frame1 = tk.Frame(root, bg="white")
frame2 = tk.Frame(root, bg="white")
frame3 = tk.Frame(root, bg="white")
frame4 = tk.Frame(root, bg="white")
# Position the frames in the root
frame1.grid(row=0, column=0, columnspan=2)
frame2.grid(row=1, column=0)
frame3.grid(row=1, column=1)
frame4.grid(row=3, column=0, columnspan=2)


## Frame 1
def addfile():
    filename = filedialog.askopenfilename(initialdir=homedir + "/Documents", title="Select File",
                                          filetypes=(("Text", "*.txt"), ("All", "*.*")))
    Input_file = filename
    label0['text'] = filename

    Ent3.insert(0,"200")
    Ent4.insert(0,"100")
    Ent5.insert(0,"20")



# Create the select button
select_button = tk.Button(frame1, text="Select File", padx=10, pady=5, fg="white", bg="#263D42", command=addfile)
select_button.grid(row=0, column=0)
label0 = tk.Label(frame1)
label0.grid(row=0, column=1)


# Frame 2
# Show the problem specifics labels that can't be changed
lable1 = tk.Label(frame2, text="Number of customers")
lable2 = tk.Label(frame2, text="Total demand")
lable1.pack()
lable2.pack()

# Frame 3
# The parameters than can be changed
lable3 = tk.Label(frame3, text="battery capacity")
lable4 = tk.Label(frame3, text="vehicle load")
lable5 = tk.Label(frame3, text="replenishment time")
Ent3 = tk.Entry(frame3)
Ent4 = tk.Entry(frame3)
Ent5 = tk.Entry(frame3)
lable3.grid(row=0, column=0, sticky="NSEW")
lable4.grid(row=1, column=0, sticky="NSEW")
lable5.grid(row=2, column=0, sticky="NSEW")
Ent3.grid(row=0, column=1,sticky="NSEW")
Ent4.grid(row=1, column=1,sticky="NSEW")
Ent5.grid(row=2, column=1,sticky="NSEW")

# Thid button will run the algorithm
run = tk.Button(root, text="Run", padx=30, pady=15, fg="white", bg="green")
run.grid(row=3, column=0, columnspan=2)

# Frame 4
# here we show the every selected route on the map, its time and energy comsumption


root.mainloop()
