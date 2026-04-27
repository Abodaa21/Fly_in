import re
from pydantic import BaseModel, Field, ValidationError
from typing import IO, Optional
from exceptions import InvalidLine


class DataValidator(BaseModel):
    nb_drones: Optional[int] = Field(default=None, gt=0)

    def validate_lines(self, f: IO[str]):
        start_count = 0
        first_time = True
        end_count = 0
        for idx, i in enumerate(f):
            idx += 1
            if not i or i.isspace() or i.startswith("#"):
                continue
            if first_time:
                pateren = r"^nb_drones:\s+(?P<nb_drones>(\d+))(?:\s+|$|#)"
                search = re.search(pateren, i)
                if search is None or int(search.group("nb_drones")) == 0:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "should be like (nb_drones: "
                                      "<strict_positive_integer>)")
                first_time = False
                DataValidator(nb_drones=int(re.search(pateren, i).group("nb_drones")))
            if re.match("start_hub:", i):
                pateren = (r"^start_hub:\s+(?P<zone_names>\w+)\s+(?P<x_coords>(?:-)?\d+)\s+"
                           r"(?P<y_coords>(?:-)?\d+)\s+(?:\[\s*((color=(?P<color>\w+)|max_drones=(?P<max_drones>\d+))(?:\s+)?)+\])?($|\s+)")
                if start_count != 0:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "the start_hub line "
                                      "have been duplicated")
                start_count += 1
        
                search = re.search(pateren, i)
                if search is None:
                    raise InvalidLine(f"Error in line{idx}:\n"
                                      "should be like (start_hub: <name> "
                                      "(not space or '-')> <x> (int)"
                                      " <y> (int) [optional]\n[color=...."
                                      "max_drones=(should be an int)]")
                
                
            elif re.match("end_hub:", i):
                pateren = (r"^end_hub:\s+(?P<zone_names>[^\s|-]+)\s+"
                           r"(?P<x_coords>(?:-)?\d+)\s+(?P<y_coords>(?:-)?\d+)"
                           r"\s+(?:\[(?:\s+)?(?:[a-z]+=(\w|_)+)?(?:\s+)?\])?(?:$|\s+)")
                if end_count != 0:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "the end_hub line "
                                      "have been duplicated")
                search = re.search(pateren, i)
                if search is None:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "should be like (end_hub: <name>"
                                      "(not space or '-')> <x> (positive int)"
                                      "<y> (positive int) [.....]")
                end_count = +1
                
import sys


try:
    with open(sys.argv[1], "r") as f:
        DataValidator().validate_lines(f)
except Exception as e:
    print({e})