import tkinter as tk

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mover Frame en Tkinter")
        self.geometry("300x300")

        self.frame_y_position = 50  # Posición inicial del frame

        # Crear el frame
        self.movable_frame = tk.Frame(self, width=200, height=100, bg="lightblue")
        self.movable_frame.place(x=50, y=self.frame_y_position)

        # Añadir un widget dentro del frame
        self.label = tk.Label(self.movable_frame, text="Soy un Frame Movible")
        self.label.pack(pady=20)

        # Botón para mover el frame hacia abajo
        self.move_button = tk.Button(self, text="Mover Frame Abajo", command=self.move_frame_down)
        self.move_button.pack(pady=20)

    def move_frame_down(self):
        # Incrementar la posición y mover el frame
        self.frame_y_position += 10
        self.movable_frame.place(y=self.frame_y_position)

if __name__ == "__main__":
    app = App()
    app.mainloop()
