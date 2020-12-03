# Este archivo contiene la implementacion de la clase Simulation (11.11.10)
""" Un objeto de la clase Simulation representa un experimento en el que
se ejecuta un algoritmo distribuido sobre una grafica de comunicaciones """

from .process import Process
from .simulator import Simulator
# ----------------------------------------------------------------------------------------

import re


class Simulation:
    """ Atributos: "engine", "graph", "table", contiene tambien un
    constructor y los metodos "setModel()", "init()", "run()" """

    def __init__(self, filename, maxtime):
        """ construye su motor de simulacion, la grafica de comunicaciones y
        la tabla de procesos """
        self.__numero_nodos = 0 
        self.engine = Simulator(maxtime)
        self._graph = []
        self.table = [[]]
        
        lineas_vacias = re.compile('\n')
        f = open(filename)
        lines = f.readlines()
        f.close()
        for line in lines:
            fields = line.split()
            neighbors = []
            if not lineas_vacias.match(line): 
                self.__numero_nodos += 1  
                for f in fields:
                    neighbors.append(int(f))
                self._graph.append(neighbors)

        for i, row in enumerate(self._graph):
            newprocess = Process(row, self.engine, i + 1)
            self.table.append(newprocess)

    def setModel(self, model, id, port=0):
        """ asocia al proceso con el modelo que debe ejecutar y viceversa """
        process = self.table[id]
        process.setModel(model, port)

    def init(self, event):
        """ inserta un evento semilla en la agenda """
        self.engine.insertEvent(event)

    def run(self):
        """ arranca el motor de simulacion """
        while self.engine.isOn():
            nextevent = self.engine.returnEvent()
            target = nextevent.target 
            time = nextevent.time
            port = nextevent.port
            nextprocess = self.table[target]
            nextprocess.setTime(time, port)
            nextprocess.receive(nextevent, port)

    @property
    def graph(self):
        return self._graph
    
    
    @property
    def numero_nodos(self):
        return self.__numero_nodos
