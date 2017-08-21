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
        
    def __str__(self):
        return "%s %s %s %s" % (self.helm, self.crew, self.class_, self.sailno)
        
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
        #self.races.sort(lambda lhs, rhs: lhs.time_ - rhs.time_)
        
    def process(self):
        hcaps = self.starting_hcaps
        print self.name
        for race in self.races:
            hcaps = race.process(hcaps)
        

class Result (object):
    FIN_NORM = "FIN_NORM"
    FIN_DNF = "FIN_DNF"
    FIN_DNS = "FIN_DNS"
    FIN_DNC = "FIN_DNC"
    FIN_RDG = "FIN_RDG"
    
    def __init__(self, et_str=None, finish=FIN_NORM):
        self.finish = finish
        self.ct_s = None
        self.place = None
        self.pts = None
        self.guest_helm = None
        self.guest_crew = None
        self.et_s = None
        self.boat = None
        self.hcap = None
        
        if finish != Result.FIN_NORM and et_str:
            raise Exception ("Elapsed time given for %s" % finish)
 
        if finish==Result.FIN_NORM:
            if not et_str:
                raise Exception ("No elapsed time give for normal finisher")
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
            
    def __str__(self):
        if self.finish == Result.FIN_NORM:
            str = "ct %ss et %ss" % (self.ct_s, self.et_s)
        elif (self.finish == Result.FIN_DNF):
            str = "DNF"
        elif (self.finish == Result.FIN_DNS):
            str = "DNS"
        elif (self.finish == Result.FIN_DNC):
            str = "DNC"
        elif (self.finish == Result.FIN_RDG):
            str = "RDG"
        return str
        
class Race (object):
    def __init__(self, name):
        self.results = {} #{boat -> Result)
        self.name = name
        
    def add_result(self, boat, result):
        self.results[boat] = result
        result.boat = boat
        
    def process(self, boats_to_hcaps):
        for boat, result in self.results.iteritems():
            if result.et_s:
                result.ct_s = int(round(result.et_s / (boats_to_hcaps[boat] / 1000.0)))
                result.hcap = boats_to_hcaps[boat]
        
        norm_finish_results = [result for result in self.results.values() if result.finish == Result.FIN_NORM]
        norm_finish_results.sort(lambda lhs, rhs: cmp(lhs.ct_s, rhs.ct_s))
        #TODO assign points for results here
        
        print "\n", self.name
        for result in norm_finish_results:
            print result.boat, result
        print "#norm finishers", len(norm_finish_results)
            
        num_relevant_finishers = int(round(float(len(norm_finish_results))*2/3))
        avg_ct_s = round(sum([r.ct_s for r in norm_finish_results[0:num_relevant_finishers]])/num_relevant_finishers)
        print "avg_ct_s (%d) from top %d finishers (ct)" % (avg_ct_s, num_relevant_finishers)
        
        print "New Hcaps:"
        boats_to_new_hcaps = boats_to_hcaps.copy()
        for boat in self.results.keys():
            result = self.results[boat]
            if result.finish != Result.FIN_NORM: continue 
            change = int(round((result.et_s/avg_ct_s*1000 - boats_to_hcaps[boat]) / 4))
            limited_change = change
            if limited_change > 20:
                limited_change = 20
            boats_to_new_hcaps[boat] = boats_to_hcaps[boat] + limited_change
            print boat, boats_to_hcaps[boat], "->", boats_to_new_hcaps[boat],
            if change != limited_change:
                print "(%d)" % change
            else:
                print 
            
        return boats_to_new_hcaps
     
    def __str__(self):
        str = "%s" % (self.name)
        for boat, result in self.results.iteritems():
            str = str + "\n%s -> %s" % (boat, result)
        return str
        
    
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

g_boats  = [
    Boat ("gp14", 13228, "Billy O'Mahony", "Damian Barnes") ,
    Boat ("w", 9331, "Jim O'Sullivan", "Kevin Donlon"),
    Boat ("w", 12000, "Margaret Hynes", "Mike Hayes"),
    Boat ("w", 12000, "Brian Park", "Mike Logan"),
    Boat ("gp14", 11000, "George FitzGerald", "Frank"),
    Boat ("rs200", 611, "Niamh Edwards", "Roisin"),
    Boat ("rs200", 449, "Hugh Ward", "Colm Ward"),
    Boat ("w", 1234, "Hugh O'Malley", "Hughscrew"),
    Boat ("x", 1234, "somalley", ""),
    Boat ("x", 1234, "briand", ""),
    Boat ("x", 1234, "sharrold", ""),
    Boat ("W", 1234, "Mike Haig", "Niamh Haig"),
    Boat ("x", 1234, "austinc", ""),
    Boat ("x", 1234, "tommys", ""),
    Boat ("x", 1234, "caroliner", ""),
    Boat ("x", 1234, "lparks", ""),
    Boat ("x", 1234, "chrisc", ""),
    Boat ("x", 1234, "tommc", ""),
    Boat ("x", 1234, "coranneh", ""),
    Boat ("x", 1234, "colmw", ""),
    Boat ("x", 1234, "margareth", ""),
]

def find_boat (str_):
    """
    For now find by name only
    """
    global g_boats
    ret_val = None
    for boat in g_boats:
        if boat.helm.lower.find(str_.lower) == 0:
            if ret_val is None:
                ret_val = boat
            else
                raise Exception ("%s matches two boats! %s and %s" % (boat, ret_val))
    return ret_val            
        
    
def main():

    series = Series ("Spring")
    for b in g_boats:
        series.add_starting_hcap(b, 1000)
        
    """
    series.add_starting_hcap(billy, 1000)
    series.add_starting_hcap(marg, 1000)
    series.add_starting_hcap(jim, 1000)
    series.add_starting_hcap(hugh, 1000)
    series.add_starting_hcap(niamh, 1000)
    series.add_starting_hcap(somalley, 1235)
    series.add_starting_hcap(briand, 1217)
    series.add_starting_hcap(sharrold, 1155)
    series.add_starting_hcap(austinc, 1121)
    series.add_starting_hcap(brianp, 1140)
    series.add_starting_hcap(tommys, 1255)
    series.add_starting_hcap(caroliner, 1183)
    series.add_starting_hcap(lparks, 1220)
    series.add_starting_hcap(chrisc, 1018)
    series.add_starting_hcap(tommc, 1165)
    series.add_starting_hcap(coranneh, 1168)
    series.add_starting_hcap(colmw, 1105)
    series.add_starting_hcap(margareth, 1073)
    """
    
    """Margaret,38.24"""
    result_regex = re.compile("?P<helm>\w+)\s*,\s*?<et_s>[0-9\.]+")
    race = None
    race_no = 0
    f = open('spring2017.csv')
    for l in f:
        l = l.lower()
        if l.find('race') == 0:
            race_no += 1
            race = Race ("Race%d" % race_no)
            continue
        mo = result_regex.match(l)
        if mo:
            boat = find_boat(mo.group('helm'))
            
            
        
        
    """
    r1 = Race("Race1")
    r1.add_result(marg, Result ("38.24"))
    r1.add_result(jim, Result ("40.25"))
    r1.add_result(hugh, Result ("46.24"))
    r1.add_result(niamh, Result ("47.45"))
    
    r2 = Race("Race2")
    r2.add_result(marg, Result ("29.09"))
    r2.add_result(jim, Result ("30.43"))
    r2.add_result(niamh, Result ("34.15"))
    """
    """
    r1 = Race("Race1")
    r1.add_result (somalley, Result("36.2"))
    r1.add_result (briand, Result("36.26"))
    r1.add_result (sharrold, Result("34.37"))
    r1.add_result (austinc, Result("33.46"))
    r1.add_result (brianp, Result("35.1"))
    r1.add_result (tommys, Result("40.43"))
    r1.add_result (caroliner, Result("39.40"))
    r1.add_result (lparks, Result(None, Result.FIN_DNF))
        
    r2 = Race("Race2")
    r2.add_result (somalley, Result("25.0"))
    r2.add_result (briand, Result("24.4"))
    r2.add_result (sharrold, Result("26.7"))
    r2.add_result (austinc, Result("23.2"))
    r2.add_result (brianp, Result("23.3"))
    r2.add_result (tommys, Result(None, Result.FIN_DNS))
    r2.add_result (caroliner, Result("23.57"))
    r2.add_result (lparks, Result(None, Result.FIN_DNF))

    r3 = Race("Race3")
    r3.add_result (chrisc, Result("34.25"))
    r3.add_result (tommc, Result("39.58"))
    r3.add_result (austinc, Result("39.6"))
    r3.add_result (tommys, Result("44.12"))
    r3.add_result (sharrold, Result("43.22"))
    r3.add_result (coranneh, Result(None, Result.FIN_DNF))

    r4 = Race("Race4")
    r4.add_result (chrisc, Result("23.0"))
    r4.add_result (tommc, Result("23.56"))
    r4.add_result (austinc, Result("23.49"))
    r4.add_result (tommys, Result("26.38"))
    r4.add_result (coranneh, Result("25.0"))

    r5 = Race("Race5")
    r5.add_result (chrisc, Result("11.53"))
    r5.add_result (colmw, Result("13.33"))
    r5.add_result (tommc, Result("15.14"))
    r5.add_result (caroliner, Result("17.46"))
    r5.add_result (coranneh, Result("18.51"))
    r5.add_result (margareth, Result("18.49"))
    r5.add_result (tommys, Result("22.12"))
    r5.add_result (lparks, Result("22.32"))
    
    r6 = Race("Race6")
    r6.add_result (chrisc, Result("17.5"))
    r6.add_result (colmw, Result("24.45"))
    r6.add_result (tommc, Result(None, Result.FIN_DNF))
    r6.add_result (caroliner, Result("23.15"))
    r6.add_result (coranneh, Result("19.16"))
    r6.add_result (margareth, Result(None, Result.FIN_DNF))
    r6.add_result (tommys, Result("27.4"))
    r6.add_result (lparks, Result(None, Result.FIN_DNS))
    
    spring.add_race(r1)
    spring.add_race(r2)
    spring.add_race(r3)
    spring.add_race(r4)
    spring.add_race(r5)
    spring.add_race(r6)
    spring.process()
    """
    
if __name__ == '__main__':
    main()
    
    
        
        
        
    
        
    
