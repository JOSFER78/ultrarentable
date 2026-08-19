import zipfile, xml.etree.ElementTree as ET

cfx_path = '/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx'
with zipfile.ZipFile(cfx_path, 'r') as z:
    xml_data = z.read('Build-Task1.xml')
    root = ET.fromstring(xml_data)
    
    print("ROOT TAG:", root.tag)
    for child in root:
        print(f"  Child: <{child.tag}> (attrib: {child.attrib})")
        if child.tag in ['Settings', 'TaskSettings', 'TradingOptions', 'StrategyOptions', 'GeneticEvolution', 'Ranking', 'RankingCriteria', 'Filtering']:
            for sub in child:
                print(f"    Sub: <{sub.tag}> {sub.attrib} {sub.text[:60] if sub.text else ''}")
