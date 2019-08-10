"""
    xccdf2json.py
    Reza Roodsari
    August 2019
    
    License:        MIT License
    Documentation:  https://github.com/rezroo/xmlutils.py.git
"""

import codecs
from lxml import etree as et
import json

import sys, traceback

class Tags:
    SE = "start"
    EE = "end"

    W3DOM = "http://www.w3.org/1999/xhtml"
    XMLNS = "http://checklists.nist.gov/xccdf/1.2"
    Domain = "{"+XMLNS+"}"
    BenchmarkTag = Domain + "Benchmark"
    TestResultTag = Domain + "TestResult"
    RuleResultTag = Domain + "rule-result"
    CheckTag = Domain + "check"
    CheckImportTag = Domain + "check-import"
    ResultTag = Domain + "result"
    ScoreTag = Domain + "score"
    IdentTag = Domain + "ident"

    ProfileTag = Domain + "Profile"
    GroupTag = Domain + "Group"
    RuleTag = Domain + "Rule"


class xccdf2json:

    def __init__(self, input_file, output_file = None, encoding='utf-8'):
        """Initialize the class with the paths to the input xml file
        and the output json file

        Keyword arguments:
        input_file -- input xml filename
        output_file -- output json filename
        encoding -- character encoding
        """

        # open the xml file for iteration
        self.context = et.iterparse(input_file, events=(Tags.SE, Tags.EE))
        self.output_file = output_file
        self.encoding = encoding

    def get_json(self):
        """
        Convert xccdf openscap xml result output to json.
        """

        iterator = iter(self.context)
        benchmark= {}
        profiles= {}
        rules= []
        ruleresults= []
        try:
          while True:
            event, root = iterator.next()
            if event == Tags.SE:
              if root.tag == Tags.BenchmarkTag:
                    assert root.nsmap[None] == Tags.XMLNS
              elif root.tag == Tags.TestResultTag:
                    benchmark = self._convert2dict(root.attrib)
                    benchmark.pop("id")
                    benchmark["hostname"] = root.find(Tags.Domain + 'target').text
                    benchmark["user"] = root.find(Tags.Domain + 'identity').text
                    benchmark["profile"] = root.find(Tags.Domain + 'profile').attrib["idref"]
#                   benchmark["score"] = root.find(Tags.Domain + 'score').text
              elif root.tag == Tags.ProfileTag:
                    profile = []
                    the_id = root.attrib["id"] 
                    for ch in root:
                        if ch.tag == Tags.Domain + 'select':
                            profile.append( self._convert2dict(ch.attrib) )
                    profiles[the_id] = profile
              elif root.tag == Tags.RuleTag:
                    while True:
                        event, child = iterator.next()
                        if (event == Tags.EE and child.tag == Tags.RuleTag):
                            break;
                    rule = {}
                    rule["id"] = root.attrib["id"]
#                   rule["selected"] = root.attrib["selected"]
                    rule["severity"] = root.attrib["severity"]
                    rule["check"] = root.find(Tags.Domain + 'title').text
                    rule["recommendation"] = ''.join( root.find(Tags.Domain + 'description').itertext() )
                    rule["justification"] = ''.join( root.find(Tags.Domain + 'rationale').itertext() )
                    rules.append(rule)
              elif root.tag == Tags.ScoreTag:
                    benchmark["score"] = root.text
              elif root.tag == Tags.RuleResultTag:
                    #No need to remember because we end on the same element
                    #elem = root # remember the root of the result
                    ruleresult = self._convert2dict(root.attrib)
                    ruleresult.pop("time")
                    while True:
                        event, root = iterator.next()
                        if (event == Tags.EE and root.tag == Tags.RuleResultTag):
                            break;
                        if event == Tags.SE:
                            if root.tag == Tags.ResultTag:
                                ruleresult["result"] = root.text
                            elif root.tag == Tags.IdentTag:
                                ruleresult["ident"] = root.text
                    ruleresults.append(ruleresult)
        except StopIteration:
            print("Event StopIteration found, done!")
        except:
            print("Exception:",sys.exc_info()[0],"occured.")
            var = traceback.format_exc()
            print var
        finally:
            benchmark["profiles"] = profiles
            benchmark["results"] = ruleresults
            benchmark["rules"] = rules
            return benchmark

    def convert(self, pretty=True):
        """
            Convert xml file to a json file

            Keyword arguments:
            pretty -- pretty print json (default=True)
        """

        resultslist = self.get_json()
        jsontext = json.dumps(resultslist, indent=(2 if pretty else None))

        # output file handle
        try:
            output = codecs.open(self.output_file, "w", encoding=self.encoding)
        except:
            print("Failed to open the output file")
            raise

        output.write(jsontext)
        output.close()

    def _convert2dict(self, cur):
        return dict(zip(cur.keys(), cur.values()))

