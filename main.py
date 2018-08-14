#!/usr/bin/env python

import time
import re
import argparse
import sys
from tabulate import tabulate

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
        self.hcap = hcap             # current/latest hcap
        self.prev_hcap = None        # the previous hcap
        self.unlim_adj = None        # the prev hcap adj before any limiting applied
        self.pre_norm_hcap = None    # the current hcap before fleet normalization applied
    
    def __repr__ (self):
        return "\nBoat (\"%(class_)s\", %(sailno)s, \"%(helm)s\", \"%(crew)s\", %(hcap)s)" % self.__dict__
        
    def __str__ (self):
        return self.helm
        #return "%s %s %s %s" % (self.helm, self.crew, self.class_, self.sailno)
        

def clean_name (name):
    """
    remove apostrophes an what nots from names
    """
    return filter(lambda char: char not in "'-.", name)

def normalize_hcaps (hcaps):
    """
    hcaps:{boat:hcap, ...}
    """
    sum_of_hcaps = sum (hcaps.values())
    num_hcaps = len(hcaps)
    average = float(sum_of_hcaps)/num_hcaps
    #print "Pre-norm avg:", average
    
    scaling_factor = num_hcaps*1000.0/sum_of_hcaps
    #print "Scaling factor:", scaling_factor
    MIN_SCALE_FACTOR = 5   # only scale if makes a diff of at least 5 hcap points
    
    if abs(scaling_factor * 1000 - 1000) < MIN_SCALE_FACTOR:
        #print "Scaling factor %0.3f too close to 1.0. Skipping re-normalization..." % scaling_factor
        return
    
    print "Avg Handicap: ", int(average)
    for boat in hcaps.keys():
        #print boat.hcap, "->"
        boat.hcap = hcaps[boat] = int(boat.hcap*scaling_factor)
        #print boat.hcap
    
    sum_of_hcaps = sum (hcaps.values())
    average = float(sum_of_hcaps)/num_hcaps
    #print "Post-norm hcap:", average

def secs_to_mmss (secs):
    if not secs:
        return "None"
    secs = int(secs)
    return "%d.%02d" % (secs/60, secs%60)
    
        
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
            if clean_name(boat.helm.lower()).find(clean_name(helm.lower())) == 0:
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
                if result.points: 
                    self.points[boat] += result.points
                    
            normalize_hcaps(hcaps)
            
            tabulate_header = ["Name", "Prev hcap", "Unlim. Adj", "Pre-Norm", "New"]
            tabulate_rows = []
            self.boats.sort(key=lambda boat: boat.helm)
            for boat in  self.boats:
                tabulate_rows.append([boat.helm, boat.prev_hcap, boat.unlim_adj, boat.pre_norm_hcap, boat.hcap])
            print tabulate (tabulate_rows, tabulate_header, tablefmt="grid")
        
        print "Calculating points for RDG..."
        # foreach boat in series
        for boat in self.boats:
            #calc average points excluding DNCs
            num_non_dncs = 0
            non_dnc_pts = 0
            for race in self.races:
                result = race.results.get(boat, None)
                #print result
                if result and result.finish not in [Result.FIN_DNC, Result.FIN_RDG]:
                    non_dnc_pts += result.points
                    num_non_dncs += 1
            avg_non_dnc_pts = None
            if num_non_dncs:
                avg_non_dnc_pts = float(non_dnc_pts)/num_non_dncs
            #print "avg_non_dnc_pts", avg_non_dnc_pts
            for race in self.races:
                result = race.results.get(boat, None)
                if result and result.finish == Result.FIN_RDG and avg_non_dnc_pts:
                    result.points = round(avg_non_dnc_pts, 1)
                    
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
        tabulate_header = ["Name"] + ["Race %d" % race.race_no for race in self.races] + ["Total"]
        
        tabulate_rows = []
        for boat, points in boats_n_points:
            tabulate_row = []
            print >> file_, boat.helm,
            tabulate_row.append(boat.helm)
            for race in self.races:
                print >> file_, sep, race.results[boat].points_anntd(),
                tabulate_row.append(race.results[boat].points_anntd())
            print >> file_, self.points[boat]
            tabulate_row.append(self.points[boat])
            tabulate_rows.append(tabulate_row)
            
        return tabulate (tabulate_rows, tabulate_header, tablefmt="grid")

class Result (object):
    FIN_NORM = ""
    FIN_DNF = "dnf"
    FIN_DNS = "dns"
    FIN_DNC = "dnc"
    FIN_RDG = "rdg"
    FIN_DSQ = "dsq"

    FIN_ORDER = [FIN_NORM, FIN_DNF, FIN_DNS, FIN_RDG, FIN_DSQ, FIN_DNC]
    
    def __init__(self, result_str=None, guest_crew=None):
        """
        result_str: ET in 'mm.ss' format or dnf,rdg, etc
        """
        
        self.finish = Result.FIN_NORM
        self.ct_s = None
        self.points = None
        self.guest_helm = None
        self.guest_crew = guest_crew
        self.et_s = None
        self.et_place = None # 1, 2, .. => 1st, 2nd, .. place "on the water"
        self.boat = None
        self.hcap = None
        
        result_str = result_str.strip()
        result_str = result_str.lower()
        if result_str in Result.FIN_ORDER:
            self.finish = result_str
        else:
            self.et_s = self.parse_et(result_str)
            
    def points_anntd(self):
        """Returns points as a string with annotation for non-normal finishes.
        e.g. 5 (RDG)"""
        rtn = str(self.points)
        if self.finish != Result.FIN_NORM:
            rtn += " (%s)" % self.finish
        return rtn
        
    def et_anntd(self):
        """Return string with ct in s followed by 'place on the water'"""
        rtn = str(secs_to_mmss(self.et_s))
        if self.et_place:
            rtn += " (%d)" % self.et_place
        return rtn
        
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
    def __init__(self, name, race_no):
        self.results = {} #{boat -> Result)
        self.name = name.strip()
        self.race_no = race_no
        
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
        norm_finish_results.sort(lambda lhs, rhs: cmp(lhs.et_s, rhs.et_s))
        for i, res in enumerate(norm_finish_results):
            res.et_place = i + 1
        norm_finish_results.sort(lambda lhs, rhs: cmp(lhs.ct_s, rhs.ct_s))
        
        #assign points for results
        #TODO handle results with tied CTs
        for n, result in enumerate(norm_finish_results):
            result.points = float(n + 1)
        
        for result in self.results.values():
            if result.finish == Result.FIN_DNF:
                result.points = len(norm_finish_results) + 1
            elif result.finish == Result.FIN_DNS:
                result.points = len(norm_finish_results) + 1
            elif result.finish == Result.FIN_DSQ:
                result.points = len(norm_finish_results) + 2
                
        #Assign DNC points
        boats_in_series = set(boats_to_hcaps.keys())
        boats_in_race = set(self.results.keys())
        boats_dnc_in_race = boats_in_series - boats_in_race

        for boat in boats_dnc_in_race:
            self.results[boat] = Result(Result.FIN_DNC)
            self.results[boat].boat = boat  # TODO boat should be param to Result ctor
            self.results[boat].points = len(norm_finish_results)+2
        
        #points for RDG are handled in Series.process() after all races are processed
        
        self.print_()
        
        #Calculate new hcaps
        num_relevant_finishers = int(round(float(len(norm_finish_results))*2/3))
        avg_ct_s = round(sum([r.ct_s for r in norm_finish_results[0:num_relevant_finishers]])/num_relevant_finishers)
        print "From top 2/3rd (%d) finishers avg ct is %ds " % (num_relevant_finishers, avg_ct_s)
        
        # Need to reset these temp items as new hcap only affects boats in *this race* but the temp items 
        # are printed after for *all* boats.
        for boat in boats_in_series:
            boat.prev_hcap = boat.hcap
            boat.unlim_adj = None
            boat.pre_norm_hcap = None
            
        boats_to_new_hcaps = boats_to_hcaps.copy()
        for boat in self.results.keys():
            result = self.results[boat]
            if result.finish != Result.FIN_NORM: continue 
            change = int(round((result.et_s/avg_ct_s*1000 - boats_to_hcaps[boat]) / 4))
            boat.unlim_adj = change
            limited_change = change
            if limited_change > 20:
                limited_change = 20
            boats_to_new_hcaps[boat] = boats_to_hcaps[boat] + limited_change
            boat.pre_norm_hcap = boats_to_hcaps[boat] + limited_change
            """
            print boat, boats_to_hcaps[boat], "->", boats_to_new_hcaps[boat],
            if change != limited_change:
                print "(%d)" % change
            else:
                print 
            """
        
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
        """
        Print results for this race. Except DNC.
        """
        #TODO prob can merge with __str__
        #print race results for everyone except non-competitors
        tabulate_header = ["Helm", "Crew", "Elapsed Time", "Hcap", "Corrected Time", "Pts"]
        tabulate_rows = []
        results_list = self.results.values()
        results_list.sort(lambda lhs, rhs: cmp(lhs, rhs))
        print "\n", self.name
        for result in results_list:
            if result.finish == Result.FIN_DNC: 
                break
            #print result.boat, result
            race_crew = result.guest_crew if result.guest_crew else result.boat.crew
            tabulate_row = [result.boat, race_crew, result.et_anntd(), result.hcap, result.ct_s, result.points_anntd()]
            tabulate_rows.append(tabulate_row)
        print tabulate(tabulate_rows, tabulate_header, tablefmt="grid")
    
def main():
    parser = argparse.ArgumentParser(description='CSC handicap system')
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
    
    # Margaret H,38.24
    #result_regex = re.compile("(?P<helm>[\w ']+)\s*,\s*(?P<result>[\w0-9\.]+)")
    result_regex = re.compile("(?P<helm>[\w ']+)\s*,\s*(?P<result>[\w0-9\.]+)\s*(,\s*(?P<guest_crew>[\w ']+))?")
    race = None
    race_no = 0
    f = open(args.series_file)
    
    # parse the series csv file. Creating races, adding results to races and adding Races to Series.
    for l in f:
        l = l.strip()
        if not l or l[0] == '#':
            continue
        #New races are introduced with a line starting with 'Race...'
        if l.lower().find('race') == 0:
            if race:
                series.add_race(race)
            race_no += 1
            race = Race ("Race#%d - %s" % (race_no, l[5:]), race_no)
            continue
        mo = result_regex.match(l)
        if mo:
            helm_name = mo.group('helm')
            boat = series.find_boat(helm_name)
            if not boat:
                raise Exception ("No boat for %s" % helm_name)
            guest_crew = mo.group('guest_crew')
            if guest_crew:
                guest_crew = guest_crew.strip()
            race.add_result(boat, Result(mo.group('result'), guest_crew))
        else:
            print "WARNING: In race '%s' can't parse result '%s'" % (race.name, l.strip())
    if race: 
        series.add_race(race)
    
    # process the Series i.e. calculate results and returning new boats[] with handicaps as per end of Series.
    boats = series.process()

    # print series results to stdout and to .csv
    results_file = file(series.name + ".res.csv", "w")
    print series.print_standings(results_file, ",")
    results_file.close()
    
    # create updated boats/hcaps file
    f = file(args.boats_out_file, 'w')
    f.write(repr(series.boats))
    f.close()
    

if __name__ == '__main__':
    main()
    
    
        
        
        
    
        
    
