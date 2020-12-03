# Este archivo contiene la implementacion de la clase Process (11.11.10)
""" Cada objeto de la clase Process representa la entidad activa que reside en
un nodo de la grafica de comunicaciones """


# ----------------------------------------------------------------------------------------

class Process:  
    """ Atributos: "neighbors", "engine", "id", "model",
    contiene tambien un constructor y los metodos "setModel()", 
    "transmit()" y "receive()" 	"""

    def __init__(self, neighbors, engine, id):
        """ asocia al proceso con su lista de vecinos, su motor de 
        simulacion y su identificador """
        self.neighbors = neighbors
        self.engine = engine
        self.id = id
        self.models = []

    def setModel(self, model, port=0):
        """ asocia al proceso con el modelo que debe ejecutar y viceversa """
        self.models.insert(port, model)
        model.setProcess(self, self.neighbors, self.id, port)
        model.init()

    def setTime(self, time, port=0):
        """ actualiza el valor del reloj local """
        model = self.models[port]
        model.setTime(time)

    def transmit(self, event):
        """ invoca al motor para insertar un evento en su agenda """
        self.engine.insertEvent(event)


    def receive(self, event, port=0):
        """ consulta a su modelo para decidir la atencion de un evento """
        model = self.models[port]
        model.receive(event)
