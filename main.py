import time
import re

class Boat (object):
    def __init__ (self, class_, sailno, helm, crew, hcap=None):
        self.class_ = class_
        self.sailno = sailno
        self.helm = helm
        self.crew = crew
        self.hcap_history = [] #[(time, hcap), ...]
        
        if hcap: self.set_hcap(hcap, time.time())
        
    def set_hcap (self, hcap, time_):
        self.hcap_history.append((time_, hcap))
        self.hcap_history.sort(lambda lhs, rhs: lhs.time_ - rhs.time_)
        
class Series (object):
    def __init__(self, name):
        pass
        self.name = name
        self.races = [] #[Race, ...]
        self.starting_hcaps = {}  #{Boat:hcap, ...}
    
    def add_starting_hcap (self, boat, hcap):
        self.starting_hcaps[boat] = hcap
    
    def add_race (self, race):
        self.races.append(race)
        self.races.sort(lambda lhs, rhs: lhs.time_ - rhs.time_)
        
    def process(self):
        hcaps = self.starting_hcaps
        for race in self.races:
            hcaps = race.process(hcaps)
            for boat, hcap in hcaps.iteritems():
                print boat.helm, hcap
        

class Result (object):
    FIN_NORM = 10000
    FIN_DNF = 10002
    FIN_DNS = 10003
    FIN_DNC = 10004
    FIN_RDG = 10005
    
    def __init__(self, et_str=None, finish=FIN_NORM):
        self.finish = finish
        self.ct_s = None
        self.place = None
        self.pts = None
        self.guest_helm = None
        self.guest_crew = None
        self.et_s = None
        if finish==Result.FIN_NORM:
            self.et_s = self.parse_et(et_str)
        
    def parse_et(self, et_str):
        """
        Convert several flavor of 'mm.ss' into seconds
        """
        splits = re.split("\.|,|:", et_str)
        if len(splits) != 2: raise Exception ("Couldn't parse '%s' as an elapsed time - too many/few delimters" % et_str)
        mm = int(splits[0])
        ss = int(splits[1])
        if not 0 <= ss < 60: raise Exception ("Couldn't parse '%s' as an elapsed time - seconds not in range 0-59")
        if mm < 0: raise Exception ("Couldn't parse '%s' as an elapsed time - minutes < 0")
        return mm*60 + ss
    
    def __cmp__(self, lhs, rhs):
        if lhs.ct_s and rhs.ct_s:
            return lhs.ct_s - rhs.ct_s
        else:
            return lhs.finish - rhs.finish
        
class Race (object):
    def __init__(self, series_num):
        self.results = {} #{boat -> Result)
        self.series = series_num
        
    def add_result(self, boat, result):
        self.results[boat] = result
        
    def process(self, boats_to_hcaps):
        for boat, result in self.results.iteritems():
            if result.et_s:
                result.ct_s = result.et_s / (boats_to_hcaps[boat] / 1000.0)
        
        norm_finish_results = [result for result in self.results.values() if result.finish == Result.FIN_NORM]
        norm_finish_results.sort(lambda lhs, rhs: lhs.ct_s - rhs.ct_s)
        num_relevant_finishers = round(len(norm_finish_results*2/3))
        avg_finishing_time = sum([r.et_s for r in [norm_finish_results[0:num_relevant_finishers]]])/num_relevant_finishers
        
        boats_to_new_hcaps = boats_to_hcaps.copy()
        for boat in boats_to_hcaps.keys():
            result = self.results[boat]
            change = (result.et_s/avg_finishing_time*1000 - boats_to_hcaps[boat]) / 4
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
    
"""
marg 38.24
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
"""

    
def main():
    billy = Boat ("gp14", 13228, "Billy", "Damian") 
    jim = Boat ("w", 9331, "Jim", "Kevin")
    marg = Boat ("w", 12000, "Margaret", "Mike")
    brian = Boat ("w", 12000, "Margaret", "Mike")
    ger = Boat ("gp14", 11000, "George", "Frank")
    niamh = Boat ("rs200", 611, "Niamh", "Roisin")
    hugh = Boat ("w", 1234, "Hugh", "HughCrew")

    spring = Series ("Spring")
    spring.add_starting_hcap(billy, 1000)
    spring.add_starting_hcap(marg, 1000)
    spring.add_starting_hcap(jim, 1000)
    spring.add_starting_hcap(hugh, 1000)
    spring.add_starting_hcap(niamh, 1000)
    
    r1 = Race("Race1")
    r1.add_result(marg, Result ("38.24"))
    r1.add_result(jim, Result ("40.25"))
    r1.add_result(hugh, Result ("46.24"))
    r1.add_result(niamh, Result ("47.45"))
    
    spring.add_race(r1)
    spring.process()
    
if __name__ == '__main__':
    main()
    
    
        
        
        
    
        
    
