import time

class Boat
    def __init__ (self, class_, sailno, helm, crew, hcap):
        self.class_ = class_
        self.sailno = sailno
        self.helm = helm
        self.crew = crew
        self.hcap_history = [] #[(time, hcap), ...]
        
        if hcap: self.set_hcap(hcap, time.time())
        
    def set_hcap (self, hcap, time_):
        self.hcap_history.append((time_, hcap))
        self.hcap_history.sort(lambda lhs, rhs: lhs.time_ - rhs.time_)
        
class Series
    def __init__(self):
        pass
        self.races = [] #[Race, ...]
		self.starting_hcaps = {}  #{Boat:hcap, ...}
    
	def add_starting_hcap (self, boat, hcap):
		self.starting_hcaps[boat] = hcap
	
    def add_race (self, race):
        self.races.append(race)
        self.races.sort(lambda lhs, rhs: lhs.time_ - rhs.time_)
        
    def process(self):
        for race in races:
            race.process()
            

class Result:
    FIN_NORM = 10000
    FIN_DNF = 10002
    FIN_DNS = 10003
    FIN_DNC = 10004
    FIN_RDG = 10005
    
    def __init__(self, et=None, finish=Result.FIN_NORM):
        self.et = et
        self.finish = finish
        self.ct = None
        self.place = None
        self.pts = None
        self.guest_helm = None
        self.guest_crew = None
        
    def __cmp__(self, lhs, rhs):
        if lhs.ct and rhs.ct:
            return lhs.ct - rhs.ct
        else:
            return lhs.finish - rhs.finish
        
class Race
    def __init__(self, series_num):
        self.results = {} #{boat -> Result)
        self.series = series_num
        
    def add_result(self, boat, result):
        self.results[boat] = result
        
    def process(self, boats_to_hcaps):
        for boat, result in self.results.iteritems():
            if result.et:
                result.ct = result.et / (boats_to_hcaps[boat] / 1000.0)
        
        norm_finish_results = [result for result in results.items() if result.finish == Results.FIN_NORM]
        norm_finish_results.sort(lambda lhs, rhs: lhs.ct - rhs.ct)
        num_relevant_finishers = round(len(norm_finish_results*2/3))
        avg_finishing_time = sum([r.et for r in [norm_finish_results[0:num_relevant_finishers]])/num_relevant_finishers
        
        boats_to_new_hcaps = boats_to_hcaps.copy()
        for boat in boats_to_hcaps.keys():
            result = self.results[boat]
            change = (result.et/avg_finishing_time*1000 - boats_to_hcaps[boat]) / 4
            if change > 20:
                change = 20
            boats_to_new_hcaps[boat] = boats_to_hcaps[boat] + change
            
        return boats_to_new_hcaps
        
        
        
g_all_boats = [
    Boat ("gp14", 13228, "Billy", "Damian", 1000 ), 
    Boat ("w", 9331, "Jim", "Kevin", 1000 ), 
    Boat ("w", 12000, "Margaret", "Mike", 1000 ), 
    Boat ("gp14", 11000, "George", "Frank", 1000 ), 
    ]
    
#marg 38.24
jim 40.25
hugh 46.24
niamh ed 47.45

marg 29.09
jim 30.43
niamh 34.15

marg 23.26
brian 24.36
hugh 23.17
des 25.22
mike h 27.03
sarah byrt 29.15

marg 22.10
des 23.3
hugh 23.0
billy 25.16
brian 25.42
mike h 29.15

marg 30.42
jim 31.15
billy 33.46
niamh ed 37.45

billy 29.5
jim 29.05
marg 29.45
niamh 39.3


    
def main():
    billy = Boat ("gp14", 13228, "Billy", "Damian", 1000 ), 
    jim = Boat ("w", 9331, "Jim", "Kevin", 1000 ), 
    marg = Boat ("w", 12000, "Margaret", "Mike", 1000 ), 
    brian = Boat ("w", 12000, "Margaret", "Mike", 1000 ), 
    ger = Boat ("gp14", 11000, "George", "Frank", 1000 ), 

    r1 = Race()
    r1.add_result(billy, Result (20*60))
    r1.add_result(jim, Result (21*60))
    r1.add_result(brian, Result (22*60))
    r1.add_result(ger, Result (23*60))
    
    r1.process()
    
    print r1
        
if __name__ == '__main__':
    main()
    
    
        
        
        
    
        
    
