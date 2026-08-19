import zipfile, xml.etree.ElementTree as ET

cfx_path = '/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx'
with zipfile.ZipFile(cfx_path, 'r') as z:
    xml_data = z.read('Build-Task1.xml')
    root = ET.fromstring(xml_data)
    
    for tag_name in ['RiskMoneyManagement', 'Rankings', 'WhatToBuild', 'Data', 'Databanks', 'CrossChecks']:
        el = root.find(tag_name)
        if el is not None:
            xml_str = ET.tostring(el, encoding='unicode')
            print(f"=== {tag_name} ===")
            print(xml_str[:1200])
            print("\n" + "="*40 + "\n")
