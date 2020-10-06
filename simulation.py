import simpy 


class Nadia_Simulation:

    def __init__(self, env):
        self.env = env
        self.scanCapacity = simpy.Resource(env, 1)


    def patientFunction(self):

        # Arrived
        arrived = self.env.now
        print(f"")

        # Scan Process
        with self.scanCapacity.request() as req:
            # Take Resource
            yield req
            
            # Scan
            yield env.timeout(10)

    def mainSimulation(self):
        for i in range(10):
            self.env.process(self.patientFunction(self))


env = simpy.Environment()
simulation = Nadia_Simulation(env)

for i in range(10):

