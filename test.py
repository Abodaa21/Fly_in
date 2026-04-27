

import re





text = "sflkslfk hif hif lsls"
print(text[5:].count("hi"))
                pateren = (r"^start_hub:\s+(?P<zone_names>\w+)\s+(?P<x_coords>(?:-)?\d+)\s+"
                           r"(?P<y_coords>(?:-)?\d+)\s+(?:\[((color=(?P<color>\w+)|zone=(?P<zone>(restricted|normal|blocked|priority))|max_drones=(?P<max_drones>\d+))(?:\s+)?)+\])?($|\s+)")