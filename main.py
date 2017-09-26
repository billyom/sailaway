#!/usr/bin/env python

import time
import re
import argparse
import sys

"""
TODO
- When boat has only RDGs and DNCs the RDGs end up as None and count as 0 towards Series total. Should be given a DNS for the RDG races in this case.
- 
"""

class Boat (object):
    def __init__ (self, class_, sailno, helm, crew, hcap=None):
        self.class_ = class_
        self.sailno = sailno
        self.helm = helm
        self.crew = crew
        self.hcap = hcap
    
    def __repr__ (self):
        return "\nBoat (\"%(class_)s\", %(sailno)s, \"%(helm)s\", \"%(crew)s\", %(hcap)s)" % self.__dict__
        
    def __str__ (self):
        return "%s %s %s %s" % (self.helm, self.crew, self.class_, self.sailno)

def rebalance_hcaps (hcaps):
    """
    hcaps:{boat:hcap, ...}
    """
    sum_of_hcaps = sum (hcaps.values())
    num_hcaps = len(hcaps)
    average = float(sum_of_hcaps)/num_hcaps
    print "average:", average
    
    """
    scaling_factor = num_hcaps*1000.0/sum_of_hcaps
    print "scaling_factor", scaling_factor
    
    for boat in hcaps.keys():
        print boat.hcap, "->"
        boat.hcap = hcaps[boat] = int(boat.hcap*scaling_factor)
        print boat.hcap
    """
    
    sum_of_hcaps = sum (hcaps.values())
    average = float(sum_of_hcaps)/num_hcaps
    print "average:", average
    
    
        
class Series (object):
    def __init__(self, name):
        pass
        self.name = name
        self.races = [] #[Race, ...]
        self.starting_hcaps = {}  #{Boat:hcap, ...}
        self.points = {}  #{Boat:points, ...}
        self.boats = []
    
    def add_boats (self, boats):
        self.boats = boats[:]
        for boat in self.boats:
            self.points[boat] = 0
    
    def find_boat (self, helm):
        """
        For now find by name only
        """
        ret_val = None
        for boat in self.boats:
            if boat.helm.lower().find(helm.lower()) == 0:
                if ret_val is None:
                    ret_val = boat
                else:
                    raise Exception ("%s matches two boats! %s and %s" % (helm, boat, ret_val))
        return ret_val
    
    def add_race (self, race):
        self.races.append(race)
        
    def process(self):
        print self.name
        hcaps = {boat:boat.hcap for boat in self.boats}
        for race in self.races:
            hcaps = race.process(hcaps)
            for boat, result in race.results.iteritems():
                if result.points: self.points[boat] += result.points
            rebalance_hcaps(hcaps)
        
        #self.boats = hcaps.keys()
        
        #Points for RDG
        #foreach boat in series
        for boat in self.boats:
            #calc average points excluding DNCs
            num_non_dncs = 0
            non_dnc_pts = 0
            for race in self.races:
                result = race.results.get(boat, None)
                print result
                if result and result.finish not in [Result.FIN_DNC, Result.FIN_RDG]:
                    non_dnc_pts += result.points
                    num_non_dncs += 1
            avg_non_dnc_pts = None
            if num_non_dncs:
                avg_non_dnc_pts = float(non_dnc_pts)/num_non_dncs
            print "avg_non_dnc_pts", avg_non_dnc_pts
            for race in self.races:
                result = race.results.get(boat, None)
                if result and result.finish == Result.FIN_RDG and avg_non_dnc_pts:
                    result.points = avg_non_dnc_pts
                    
        for race in self.races:
            race.print_()
            
        for boat in self.boats:
            boat.hcap = hcaps[boat]
            
        return self.boats
            
    def print_standings (self, file_=sys.stdout, sep="\t"):
        boats_n_points = [(boat, points) for boat, points in self.points.iteritems()]
        boats_n_points.sort(cmp=None, key=lambda tuple: tuple[1])
        
        for race in self.races:
            print >> file_, sep, race.name,
        print >> file_, sep, "Total"
        
        for boat, points in boats_n_points:
            print >> file_, boat.helm,
            for race in self.races:
                print >> file_, sep, race.results[boat].points,
            print >> file_, self.points[boat]

class Result (object):
    FIN_NORM = ""
    FIN_DNF = "dnf"
    FIN_DNS = "dns"
    FIN_DNC = "dnc"
    FIN_RDG = "rdg"

    FIN_ORDER = [FIN_NORM, FIN_DNF, FIN_DNS, FIN_RDG, FIN_DNC]
    
    def __init__(self, result_str=None):
        """
        result_str: ET in 'mm.ss' format or dnf,rdg, etc
        """
        
        self.finish = Result.FIN_NORM
        self.ct_s = None
        self.points = None
        self.guest_helm = None
        self.guest_crew = None
        self.et_s = None
        self.boat = None
        self.hcap = None
        
        result_str = result_str.lower()
        if result_str in Result.FIN_ORDER:
            self.finish = result_str
        else:
            self.et_s = self.parse_et(result_str)
            
        
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
    
    def __cmp__(self, rhs):
        if self.ct_s and rhs.ct_s:
            return self.points - rhs.points
        else:
            return Result.FIN_ORDER.index(self.finish) - Result.FIN_ORDER.index(rhs.finish)
            
    def __str__(self):
        if self.finish == Result.FIN_NORM:
            str = "%ss @%d %ss" % (self.ct_s, self.hcap, self.et_s)
        elif (self.finish == Result.FIN_DNF):
            str = "DNF"
        elif (self.finish == Result.FIN_DNS):
            str = "DNS"
        elif (self.finish == Result.FIN_DNC):
            str = "DNC"
        elif (self.finish == Result.FIN_RDG):
            str = "RDG"
        
        if self.points:
            str += " %.1f" % self.points
        else:
            str += " -"
        
        return str
        
        
class Race (object):
    def __init__(self, name):
        self.results = {} #{boat -> Result)
        self.name = name
        
    def add_result(self, boat, result):
        self.results[boat] = result
        result.boat = boat
        
    def process(self, boats_to_hcaps):
        #calc corrected times
        for boat, result in self.results.iteritems():
            if result.et_s:
                result.hcap = boats_to_hcaps[boat]
                result.ct_s = int(round(result.et_s / (result.hcap / 1000.0)))
        
        norm_finish_results = [result for result in self.results.values() if result.finish == Result.FIN_NORM]
        norm_finish_results.sort(lambda lhs, rhs: cmp(lhs.ct_s, rhs.ct_s))
        
        #assign points for results
        #TODO handle results with tied CTs
        for n, result in enumerate(norm_finish_results):
            result.points = float(n + 1)
        
        for result in self.results.values():
            if result.finish == Result.FIN_DNF:
                result.points = len(norm_finish_results) + 1
            elif result.finish == Result.FIN_DNS:
                result.points = len(norm_finish_results) + 2
                
        #Assign DNC points
        boats_in_series = set(boats_to_hcaps.keys())
        boats_in_race = set(self.results.keys())
        boats_dnc_in_race = boats_in_series - boats_in_race

        for boat in boats_dnc_in_race:
            self.results[boat] = Result(Result.FIN_DNC)
            self.results[boat].boat = boat  # TODO boat should be param to Result ctor
            self.results[boat].points = len(norm_finish_results)+3
        
        #points for RDG are handled in Series.process() after all races are processed
        
        self.print_()
        
        #Calculate new hcaps
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
        
        # change boat.hcap field also
        for boat, hcap in boats_to_new_hcaps.iteritems():
            boat.hcap = hcap
            
        return boats_to_new_hcaps
     
    def __str__(self):
        str = "%s" % (self.name)
        for boat, result in self.results.iteritems():
            str = str + "\n%s -> %s" % (boat, result)
        return str
        
    def print_(self):
        #TODO prob can merge with __str__
        #print race results for everyone except non-competitors
        results_list = self.results.values()
        results_list.sort(lambda lhs, rhs: cmp(lhs, rhs))
        print "\n", self.name
        for result in results_list:
            if result.finish == Result.FIN_DNC: break
            print result.boat, result
    
    
def main():
    parser = argparse.ArgumentParser(description='Simulate OVS EMC')
    parser.add_argument('--series', '-s', dest='series_file',
                       help='Results csv for a series')
    parser.add_argument('--iboats', '-i', dest='boats_in_file',
                       help='Starting boats db')
    parser.add_argument('--oboats', '-o', dest='boats_out_file',
                       help='Boats db after series')
    parser.add_argument('--results', '-r', dest='results_file',  type=bool,
                       help='Results file')

    args = parser.parse_args()

    boats_txt = file(args.boats_in_file).read()
    iboats = eval(boats_txt)
        
    series = Series (args.series_file.split('.')[0])
    series.add_boats(iboats)
    
    # Margaret,38.24
    result_regex = re.compile("(?P<helm>[\w ']+)\s*,\s*(?P<result>[\w0-9\.]+)")
    race = None
    race_no = 0
    f = open(args.series_file)
    for l in f:
        l = l.lower()
        if l.find('race') == 0:
            if race: series.add_race(race)
            race_no += 1
            race = Race ("Race%d" % race_no)
            continue
        mo = result_regex.match(l)
        if mo:
            helm_name = mo.group('helm')
            boat = series.find_boat(helm_name)
            if not boat:
                raise Exception ("No boat for %s" % helm_name)
            race.add_result(boat, Result(mo.group('result')))
        elif l.strip():
            print "WARNING: can't parse result '%s'" % l.strip()
    if race: series.add_race(race)
    
    boats = series.process()
    
    series.print_standings()
    
    results_file = file(series.name + ".res.csv", "w")
    series.print_standings(results_file, ",")
    results_file.close()
    
    f = file(args.boats_out_file, 'w')
    f.write(repr(series.boats))
    f.close()
    

if __name__ == '__main__':
    main()
    
    
        
        
        
    
        
    