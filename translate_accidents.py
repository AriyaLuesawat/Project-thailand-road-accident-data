#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translate Thai road-accident CSVs while preserving identifiers and row order."""

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
OUT = ROOT / "Translated_data"
OUT.mkdir(exist_ok=True)

HEADERS = {
    "ปีที่เกิดเหตุ": "Accident_Year", "วันที่เกิดเหตุ": "Accident_Date",
    "เวลา": "Accident_Time", "วันที่รายงาน": "Report_Date", "เวลาที่รายงาน": "Report_Time",
    "หน่วยงาน": "Agency", "สายทางหน่วยงาน": "Agency_Road_Type", "รหัสสายทาง": "Route_Code",
    "สายทาง": "Road_Name", "ก.ม.": "Kilometer", "KM": "Kilometer", "จังหวัด": "Province",
    "รถคันที่ 1": "First_Vehicle", "รถคันที่1": "First_Vehicle",
    "บริเวณที่เกิดเหตุ/ลักษณะทาง": "Accident_Location_Road_Geometry",
    "บริเวณที่เกิดเหตุ": "Accident_Location", "มูลเหตุสันนิษฐาน": "Presumed_Cause",
    "ลักษณะการเกิดอุบัติเหตุ": "Accident_Type", "ลักษณะการเกิดเหตุ": "Accident_Type",
    "จำนวนรถที่เกิดเหตุ (รวมคันที่ 1)": "Number_of_Vehicles_Involved",
    "จำนวนผู้เสียชีวิต": "Fatalities", "ผู้เสียชีวิต": "Fatalities",
    "รวมจำนวนผู้บาดเจ็บ": "Total_Injuries", "ผู้บาดเจ็บสาหัส": "Serious_Injuries",
    "ผู้บาดเจ็บเล็กน้อย": "Minor_Injuries", "สภาพอากาศ": "Weather",
    "รถที่เกิดเหตุ": "Vehicles_Involved", "รถและคนที่เกิดเหตุ": "Vehicles_and_People_Involved",
    "รถจักรยานยนต์": "Motorcycles", "รถสามล้อเครื่อง": "Motorized_Three_Wheelers",
    "รถยนต์นั่งส่วนบุคคล": "Private_Cars", "รถตู้": "Vans",
    "รถปิคอัพโดยสาร": "Passenger_Pickups", "รถโดยสารมากกว่า4ล้อ": "Buses_Over_4_Wheels",
    "รถปิคอัพบรรทุก4ล้อ": "Four_Wheel_Cargo_Pickups", "รถบรรทุก6ล้อ": "Six_Wheel_Trucks",
    "รถบรรทุกไม่เกิน10ล้อ": "Trucks_Up_To_10_Wheels", "รถบรรทุกมากกว่า10ล้อ": "Trucks_Over_10_Wheels",
    "รถอีแต๋น": "Farm_Vehicles", "รถอื่นๆ": "Other_Vehicles", "คนเดินเท้า": "Pedestrians",
}

PROVINCES = dict(zip(
    "กระบี่ กรุงเทพมหานคร กาญจนบุรี กาฬสินธุ์ กำแพงเพชร ขอนแก่น จันทบุรี ฉะเชิงเทรา ชลบุรี ชัยนาท ชัยภูมิ ชุมพร ตรัง ตราด ตาก นครนายก นครปฐม นครพนม นครราชสีมา นครศรีธรรมราช นครสวรรค์ นนทบุรี นราธิวาส น่าน บึงกาฬ บุรีรัมย์ ปทุมธานี ประจวบคีรีขันธ์ ปราจีนบุรี ปัตตานี พระนครศรีอยุธยา พะเยา พังงา พัทลุง พิจิตร พิษณุโลก ภูเก็ต มหาสารคาม มุกดาหาร ยะลา ยโสธร ร้อยเอ็ด ระนอง ระยอง ราชบุรี ลพบุรี ลำปาง ลำพูน ศรีสะเกษ สกลนคร สงขลา สตูล สมุทรปราการ สมุทรสงคราม สมุทรสาคร สระบุรี สระแก้ว สิงห์บุรี สุพรรณบุรี สุราษฎร์ธานี สุรินทร์ สุโขทัย หนองคาย หนองบัวลำภู อำนาจเจริญ อุดรธานี อุตรดิตถ์ อุทัยธานี อุบลราชธานี อ่างทอง เชียงราย เชียงใหม่ เพชรบุรี เพชรบูรณ์ เลย แพร่ แม่ฮ่องสอน".split(),
    "Krabi Bangkok Kanchanaburi Kalasin Kamphaeng_Phet Khon_Kaen Chanthaburi Chachoengsao Chon_Buri Chai_Nat Chaiyaphum Chumphon Trang Trat Tak Nakhon_Nayok Nakhon_Pathom Nakhon_Phanom Nakhon_Ratchasima Nakhon_Si_Thammarat Nakhon_Sawan Nonthaburi Narathiwat Nan Bueng_Kan Buri_Ram Pathum_Thani Prachuap_Khiri_Khan Prachin_Buri Pattani Phra_Nakhon_Si_Ayutthaya Phayao Phangnga Phatthalung Phichit Phitsanulok Phuket Maha_Sarakham Mukdahan Yala Yasothon Roi_Et Ranong Rayong Ratchaburi Lop_Buri Lampang Lamphun Si_Sa_Ket Sakon_Nakhon Songkhla Satun Samut_Prakan Samut_Songkhram Samut_Sakhon Saraburi Sa_Kaeo Sing_Buri Suphan_Buri Surat_Thani Surin Sukhothai Nong_Khai Nong_Bua_Lam_Phu Amnat_Charoen Udon_Thani Uttaradit Uthai_Thani Ubon_Ratchathani Ang_Thong Chiang_Rai Chiang_Mai Phetchaburi Phetchabun Loei Phrae Mae_Hong_Son".replace("_", " ").split("  ")
))
# The split above is intentionally replaced with an explicit standards list below.
PROVINCES = {
 "กระบี่":"Krabi","กรุงเทพมหานคร":"Bangkok","กาญจนบุรี":"Kanchanaburi","กาฬสินธุ์":"Kalasin","กำแพงเพชร":"Kamphaeng Phet","ขอนแก่น":"Khon Kaen","จันทบุรี":"Chanthaburi","ฉะเชิงเทรา":"Chachoengsao","ชลบุรี":"Chon Buri","ชัยนาท":"Chai Nat","ชัยภูมิ":"Chaiyaphum","ชุมพร":"Chumphon","ตรัง":"Trang","ตราด":"Trat","ตาก":"Tak","นครนายก":"Nakhon Nayok","นครปฐม":"Nakhon Pathom","นครพนม":"Nakhon Phanom","นครราชสีมา":"Nakhon Ratchasima","นครศรีธรรมราช":"Nakhon Si Thammarat","นครสวรรค์":"Nakhon Sawan","นนทบุรี":"Nonthaburi","นราธิวาส":"Narathiwat","น่าน":"Nan","บึงกาฬ":"Bueng Kan","บุรีรัมย์":"Buri Ram","ปทุมธานี":"Pathum Thani","ประจวบคีรีขันธ์":"Prachuap Khiri Khan","ปราจีนบุรี":"Prachin Buri","ปัตตานี":"Pattani","พระนครศรีอยุธยา":"Phra Nakhon Si Ayutthaya","พะเยา":"Phayao","พังงา":"Phangnga","พัทลุง":"Phatthalung","พิจิตร":"Phichit","พิษณุโลก":"Phitsanulok","ภูเก็ต":"Phuket","มหาสารคาม":"Maha Sarakham","มุกดาหาร":"Mukdahan","ยะลา":"Yala","ยโสธร":"Yasothon","ร้อยเอ็ด":"Roi Et","ระนอง":"Ranong","ระยอง":"Rayong","ราชบุรี":"Ratchaburi","ลพบุรี":"Lop Buri","ลำปาง":"Lampang","ลำพูน":"Lamphun","ศรีสะเกษ":"Si Sa Ket","สกลนคร":"Sakon Nakhon","สงขลา":"Songkhla","สตูล":"Satun","สมุทรปราการ":"Samut Prakan","สมุทรสงคราม":"Samut Songkhram","สมุทรสาคร":"Samut Sakhon","สระบุรี":"Saraburi","สระแก้ว":"Sa Kaeo","สิงห์บุรี":"Sing Buri","สุพรรณบุรี":"Suphan Buri","สุราษฎร์ธานี":"Surat Thani","สุรินทร์":"Surin","สุโขทัย":"Sukhothai","หนองคาย":"Nong Khai","หนองบัวลำภู":"Nong Bua Lam Phu","อำนาจเจริญ":"Amnat Charoen","อุดรธานี":"Udon Thani","อุตรดิตถ์":"Uttaradit","อุทัยธานี":"Uthai Thani","อุบลราชธานี":"Ubon Ratchathani","อ่างทอง":"Ang Thong","เชียงราย":"Chiang Rai","เชียงใหม่":"Chiang Mai","เพชรบุรี":"Phetchaburi","เพชรบูรณ์":"Phetchabun","เลย":"Loei","แพร่":"Phrae","แม่ฮ่องสอน":"Mae Hong Son"
}
PROVINCES["อยุธยา"] = "Phra Nakhon Si Ayutthaya"

AGENCY = {"กรมทางหลวง":"Department of Highways","กรมทางหลวงชนบท":"Department of Rural Roads","การทางพิเศษแห่งประเทศไทย":"Expressway Authority of Thailand"}
ROAD_TYPE = {"ทางหลวง":"Highway","ทางหลวงชนบท":"Rural Road","การทางพิเศษ":"Expressway"}
WEATHER = {"แจ่มใส":"Clear","ฝนตก":"Rain","มืดครึ้ม":"Overcast","มีหมอก/ควัน/ฝุ่น":"Fog, smoke, or dust","ภัยธรรมชาติ เช่น พายุ น้ำท่วม":"Natural hazard (e.g. storm or flood)","ดินถล่ม":"Landslide","อื่นๆ":"Other"}
VEHICLE = {"คนเดินเท้า":"Pedestrian","รถจักรยาน":"Bicycle","รถจักรยานยนต์":"Motorcycle","รถตู้":"Van","รถบรรทุก 6 ล้อ":"6-wheel truck","รถบรรทุกมากกว่า 10 ล้อ (รถพ่วง)":"Truck over 10 wheels (trailer)","รถบรรทุกมากกว่า 6 ล้อ ไม่เกิน 10 ล้อ":"Truck with 7–10 wheels","รถปิคอัพบรรทุก 4 ล้อ":"4-wheel cargo pickup","รถปิคอัพโดยสาร":"Passenger pickup","รถยนต์นั่งส่วนบุคคล/รถยนต์นั่งสาธารณะ":"Private/public passenger car","รถสามล้อ":"Three-wheeled vehicle","รถสามล้อเครื่อง":"Motorized three-wheeler","รถอีแต๋น/เพื่อการเกษตร":"Farm vehicle","รถโดยสารขนาดใหญ่":"Large bus","อื่นๆ":"Other"}

LOCATION_PARTS = {
 "จุดกลับรถต่างระดับ":"Grade-separated U-turn","จุดตัดทางรถไฟ":"Railway crossing","ทางคนเดินเท้า":"Pedestrian path","ทางจักรยาน":"Bicycle path","ทางตรง":"Straight road","ทางม้าลาย/คนเดินข้าม":"Pedestrian crossing","ทางม้าลาย":"Zebra crossing","ทางยกระดับ":"Elevated road","ทางรถไฟตัดผ่าน":"Railway crossing","ทางรถจักรยานยนต์":"Motorcycle lane","ทางร่วม":"Road junction","ทางลอด":"Underpass","ทางสามแยก (T)":"T-junction","ทางสามแยก(T)":"T-junction","ทางสามแยก (Y)":"Y-junction","ทางสามแยก(Y)":"Y-junction","ทางสี่แยก":"Four-way intersection","ทางเชื่อมเข้าบริเวณหน้าโรงเรียน":"Access road in front of a school","ทางเชื่อมเข้าพื้นที่สาธารณะ/เชิงพาณิชย์":"Access road to a public/commercial area","ทางเชื่อมเข้าพื้นที่ส่วนบุคคล":"Access road to private property","ทางแยกต่างระดับ / Ramps":"Interchange/ramp","ทางแยกต่างระดับ/Ramps":"Interchange/ramp","ทางแยกรูปตัว +":"Cross intersection","ทางแยกรูปตัว T":"T-junction","ทางแยกรูปตัว Y":"Y-junction","ทางโค้งกว้าง":"Gentle curve","ทางโค้งปกติ":"Normal curve","ทางโค้งหักศอก":"Sharp curve","มีการเปลี่ยนความกว้างช่องจราจร":"Change in lane width","มีการเปลี่ยนจำนวนช่องจราจร":"Change in number of lanes","วงเวียน":"Roundabout","สถานี/จุดขึ้นลงระบบขนส่งสาธารณะ":"Public transport station/stop","สะพาน (สะพานข้ามแม่น้ำ/ข้ามคลอง)":"Bridge (river/canal crossing)","สะพาน":"Bridge","อื่นๆ":"Other","เข้าพื้นที่สาธารณะหรือเชิงพานิชย์":"Entrance to public/commercial area","เข้าพื้นที่ส่วนบุคคล":"Entrance to private property","เข้าสถานศึกษา / สถานที่ราชการ":"Entrance to an educational institution/government office","ที่ราบ":"level grade","ที่ลาดชัน":"steep grade","บนช่วงลาดชัน":"on a grade","ยอดโค้ง":"crest vertical curve","ก้นโค้ง":"sag vertical curve","โค้งดิ่ง/ที่ลาดชัน":"vertical curve/grade","ไม่มีความลาดชัน/ที่ราบ":"no grade/level grade","ไม่มีความลาดชัน":"no grade"
}

CAUSE = {
 "การกระทำที่สุ่มเสี่ยงบนถนน":"Risky behavior on the road","การซ่อม/สร้างบนสายทาง":"Road construction/repair","กำลังเครื่องยนต์ไม่เพียงพอ":"Insufficient engine power","ขับขี่ช้าเกินเนื่องจากลักษณะของยานพาหนะ (เช่น แทรคเตอร์)":"Driving too slowly due to vehicle characteristics (e.g. tractor)","ขับขี่ย้อนศร":"Driving against traffic","ขับชิดขอบทางขวามากเกินไป":"Driving too close to the right edge","ขับชิดซ้ายมากเกินไป":"Driving too far left","ขับรถกระชั้นชิด":"Following too closely","ขับรถคร่อมเส้นแบ่งทิศทาง":"Straddling the center line","ขับรถชิดขวามากไป":"Driving too far right","ขับรถชิดซ้ายมากเกินไป":"Driving too far left","ขับรถช้าลง":"Slowing down","ขับรถตามกระชั้นชิด":"Following too closely","ขับรถผิดช่องทาง":"Driving in the wrong lane","ขับรถย้อนศร":"Driving against traffic","ขับรถเร็วเกินอัตรากำหนด":"Exceeding the speed limit","ขับรถเร็วเกินอัตราที่กำหนด":"Exceeding the speed limit","ขับรถไม่ชำนาญ / ไม่เป็น":"Inexperienced/unable to drive","ขับรถไม่เปิดไฟ / ไม่ใช้แสงสว่างตามกำหนด":"Driving without required lights","ขับรถไม่เปิดไฟ/ไม่ใช้แสงสว่างตามกำหนด":"Driving without required lights","ข้ามถนนโดยมีรถจอดหรือวัตถุข้างทางบดบังผู้ขับขี่":"Crossing where parked vehicles or roadside objects obstruct the driver's view","คน/รถ/สัตว์ตัดหน้ากระชั้นชิด":"Person, vehicle, or animal suddenly cut in front","ความประมาท/เร่งรีบ (วิ่งตัดหน้า)":"Carelessness/hurrying (running across traffic)","ความเมื่อยล้า":"Fatigue","ถนนชำรุด":"Damaged road","ถนนลื่น":"Slippery road","ถนนลื่น (เนื่องจากสภาพอากาศ)":"Slippery road (weather-related)","ถนนแคบ":"Narrow road","ทางโค้งอันตราย":"Dangerous curve","ทำงานบนถนน":"Working on the road","นั่งบุคคลขับรถย้อนทิศทางจราจร":"Passenger riding while vehicle travels against traffic","บรรทุกสูงเกินกำหนด":"Load exceeds height limit","บรรทุกเกินอัตรา":"Overloading","ปัญหาทางสายตา":"Vision problem","ป้ายจราจรชำรุด":"Damaged traffic sign","ป้ายจราจรถูกบดบัง":"Obscured traffic sign","ผิวถนนสภาพแย่หรือชำรุด":"Poor or damaged road surface","ผู้ขับขี่ไม่เห็นเสาไฟส่องสว่าง":"Driver did not see the lighting pole","ฝาตู้เก็บของด้านข้างเปิด":"Side storage compartment door open","ฝ่าฝืนป้ายหยุดขณะออกจากทางร่วมทางแยก":"Failed to obey stop sign when entering from a junction","ฝ่าฝืนป้ายหยุดขณะออกจากทางร่วมแยก":"Failed to obey stop sign when entering from a junction","ฝ่าฝืนสัญญาณไฟ / เครื่องหมายจราจร":"Disobeyed traffic signal/sign","ฝ่าฝืนสัญญาณไฟ/เครื่องหมายจราจร":"Disobeyed traffic signal/sign","พวงมาลัยชำรุด":"Defective steering wheel","มีกองวัสดุ/สิ่งกีดขวาง":"Pile of material/obstruction","มีการตัดหน้าระยะกระชั้นชิด":"Sudden cut-in","มีคราบสะสมบนผิวถนน เช่น โคลน น้ำมัน":"Deposits on road surface, such as mud or oil","มีสิ่งกีดขวางบนทางหลวง (วัสดุหรือสัตว์)":"Obstruction on highway (material or animal)","มีสิ่งบดบังการมองเห็น":"Visibility obstruction","มีสิ่งรบกวนภายนอก เช่น ป้ายจราจรมีสีที่สว่างเกินไป":"External distraction, such as an excessively bright traffic sign","มีสิ่งรบกวนภายนอกรถ":"Distraction outside the vehicle","มีสิ่งรบกวนภายในรถ":"Distraction inside the vehicle","มีสิ่งรบกวนภายในรถ เช่น มีเด็ก มีสัตว์ภายในรถ":"Distraction inside the vehicle, such as a child or animal","มึนเมาจากแอลกอฮอล์":"Alcohol intoxication","ยางรถยนต์ชำรุด":"Defective tire","ยางเสื่อมสภาพ/ยางแตก":"Worn/burst tire","ยานพาหนะเคลื่อนที่ช้า":"Slow-moving vehicle","รถมีความสูงเกินกำหนด":"Vehicle exceeds height limit","รถเสียไม่แสดงเครื่องหมาย/สัญญาณตามที่กำหนด":"Disabled vehicle without required warning sign/signal","รถเสียไม่แสดงเครื่องหมายหรือสัญญาณไฟที่กำหนด":"Disabled vehicle without required warning sign/light","ระบบบังขับเลี้ยวชำรุด":"Defective steering system","ระบบบังคับเลี้ยวขัดข้อง":"Steering system failure","ระบบสัญญาณไฟจราจรขัดข้อง":"Traffic signal system failure","ระบบห้ามล้อขัดข้อง/ระบบเบรกชำรุด":"Brake system failure","ระบบไฟขัดข้องในห้องเครื่อง":"Electrical failure in engine compartment","ระบบไฟฟ้ขัดข้อง":"Electrical system failure","ระบบไฟฟ้าของยานพาหนะขัดข้อง":"Vehicle electrical system failure","ระบบไฟฟ้าขัดข้อง":"Electrical system failure","ระยะการมองเห็นไม่เพียงพอ":"Insufficient sight distance","ระยะปลอดภัยข้างทางไม่เพียงพอ":"Insufficient roadside clear zone","ระยะมองเห็นจำกัด":"Limited sight distance","ละสายตาจากการขับขี่":"Eyes off the road","ลักษณะของถนน เช่น เป็นทางโค้ง, เนินเขา, ผิวทางแคบ":"Road characteristics, such as a curve, hill, or narrow surface","สัญญาณไฟจราจรชำรุด":"Defective traffic signal","สูญเสียการควบคุม":"Loss of control","หยุดรถกะทันหัน":"Sudden stop","หลับใน":"Fell asleep at the wheel","หางพ่วงหลุด":"Trailer detached","อาการป่วย หรือการไร้ความสามารถทางประสาทหรือร่างกาย":"Illness or neurological/physical incapacity","อาการป่วยหรือการไร้ความสามารถทางประสาทหรือร่างกาย":"Illness or neurological/physical incapacity","อื่นๆ":"Other","อุปกรณ์นำทางชำรุด":"Defective navigation equipment","อุปกรณ์ยานพาหนะบกพร่อง":"Vehicle equipment defect","อุปกรณ์ยานพาหนะบกพร่อง (ระบุ)":"Vehicle equipment defect (specified)","เข้าผิดช่อง":"Entered wrong lane","เข้าผิดช่องทางผิด":"Entered wrong lane","เครื่องยนต์ขัดข้อง":"Engine failure","เบครกระทันหัน":"Sudden braking","เบรกกะทันหัน":"Sudden braking","เบรคกระทันหัน":"Sudden braking","เบรคกะทันหัน":"Sudden braking","เบรคชำรุด":"Defective brakes","เปลี่ยนช่องทางกะทันหัน":"Sudden lane change","เมาสุรา":"Drunk driving","เส้นแบ่งทิศทางจราจรชำรุด":"Damaged center line marking","แซงรถอย่างผิดกฎหมาย":"Illegal overtaking","แสงสว่างไม่เพียงพอ":"Insufficient lighting","แสงสว่างไม่เพียงพอหรือทัศนวิสัยกลางคืนไม่ดี":"Insufficient lighting or poor night visibility","โรคประจำตัว":"Underlying medical condition","ใช้สารออกฤทธิ์ต่อจิตและประสาท":"Use of psychoactive substances","ใช้โทรศัพท์ขณะขับรถ":"Using a phone while driving","ใช้โทรศัพท์เคลื่อนที่ขณะขับรถ":"Using a mobile phone while driving","ไฟฟ้าแสงสว่างชำรุด":"Defective road lighting","ไฟส่องสว่างชำรุด":"Defective lighting","ไม่ขับรถในช่องทางเดินรถซ้ายสุดในถนนที่มี 4 ช่องทาง":"Failure to use the leftmost lane on a four-lane road","ไม่คุ้นชินกับยานพาหนะ เช่น กรณีเช่ารถ":"Unfamiliar with the vehicle, e.g. a rental vehicle","ไม่คุ้นเคยกับการขับขี่ด้านซ้าย":"Unfamiliar with left-side driving","ไม่คุ้นเคยกับการขับขี่ด้านซ้าย เช่น กรณีชาวต่างชาติ":"Unfamiliar with left-side driving, e.g. a foreign driver","ไม่คุ้นเคยเส้นทาง/ขับรถไม่ชำนาญ":"Unfamiliar with route/inexperienced driving","ไม่มีป้ายจราจร":"No traffic sign","ไม่มีมูลเหตุสันนิษฐานที่เกี่ยวข้องด้านสภาพสายทาง":"No presumed cause related to road conditions","ไม่มีระบบสัญญาณไฟจราจร":"No traffic signal system","ไม่มีเส้นแบ่งทิศทางจราจร":"No center line marking","ไม่ยอมให้รถที่มีสิทธิ์ไปก่อน":"Failed to yield right of way","ไม่ให้สัญญาณชะลอ / เลี้ยว":"Failed to signal slowing/turning","ไม่ให้สัญญาณชะลอ/เลี้ยว":"Failed to signal slowing/turning","ไม่ให้สัญญาณเข้าจอด หรือออกจากที่จอด":"Failed to signal when entering/leaving parking","ไม่ให้สัญญาณเข้าจอด/ออกจากที่จอด":"Failed to signal when entering/leaving parking","ไม่ให้สิทธิรถที่มาก่อนผ่านทาง เช่น ทางแยก":"Failed to yield to a vehicle with priority, e.g. at an intersection"
}

ACCIDENT_EXACT = {
 "ชนขณะแซง":"Collision while overtaking","ชนขณะแซงชนเข้าข้างหน้า":"Collision while overtaking; struck the front","ชนคนเดินเท้า":"Pedestrian collision","ชนคนเดินเท้าชนจากฝั่งซ้าย":"Pedestrian collision from the left","ชนด้านข้าง":"Side collision","ชนทางเชื่อม":"Collision at an access road","ชนท้าย":"Rear-end collision","ชนท้าย (ช่องจราจรเดียวกัน)":"Rear-end collision (same lane)","ชนท้ายชนคนบนถนน":"Rear-end collision; struck a person on the road","ชนท้ายรถขณะเลี้ยวกลับรถ":"Rear-ended a vehicle making a U-turn","ชนประสานงา (ไม่ใช่การแซง)":"Head-on collision (not while overtaking)","ชนปาดหน้า":"Cut-in collision","ชนป้าย/วัสดุงานทาง/วัสดุที่กองอยู่ ชั่วคราว":"Collision with a sign, roadwork material, or temporary material pile","ชนรถขณะเปลี่ยนช่องจราจรทางขวา  (ไม่ใช่การแซง)":"Collision while changing to the right lane (not overtaking)","ชนรถขณะเปลี่ยนช่องจราจรทางซ้าย  (ไม่ใช่การแซง)":"Collision while changing to the left lane (not overtaking)","ชนรถที่กำลังเปลี่ยนช่องจราจร":"Collision with a vehicle changing lanes","ชนรถที่จอดบนถนน":"Collision with a vehicle parked on the road","ชนรถที่ออกจากที่จอด":"Collision with a vehicle leaving a parking space","ชนรถฝั่งตรงข้ามขณะแซง":"Collision with oncoming vehicle while overtaking","ชนรถไฟ":"Train collision","ชนสัตว์":"Animal collision","ชนสิ่งกีดขวาง (บนผิวจราจร)":"Collision with an obstruction on the carriageway","ชนสิ่งกีดขวางบนถนน":"Collision with an obstruction on the road","ชนสิ่งของ":"Collision with an object","ชนสิ่งของ/รถที่จอดอยู่ ตอนกลับรถ":"Collision with an object/parked vehicle while making a U-turn","ชนสิ่งของที่บรรทุกตกหล่น/ยื่นออกนอกตัวถัง":"Collision with fallen/protruding cargo","ชนเกาะกลาง รวมถึงเสาไฟ":"Collision with median, including a lighting pole","ชนเป็นมุมบริเวณทางแยก":"Angle collision at an intersection","ชนในทิศทางตรงกันข้าม (ไม่ใช่การแซง)":"Opposing-direction collision (not overtaking)","ชนในทิศทางตรงกันข้าม (ไม่ใช่การแซง)ชนจากฝั่งขวา":"Opposing-direction collision (not overtaking), impact from the right","ตกจากรถ":"Fell from vehicle","ถูกชน เพราะแซงซ้าย":"Hit due to overtaking on the left","ถูกชนท้ายขณะเลี้ยวขวา":"Rear-ended while turning right","ถูกชนท้ายขณะเลี้ยวซ้าย":"Rear-ended while turning left","พลิกคว่ำ/ตกถนนในทางตรง":"Overturned/ran off road on a straight section","พลิกคว่ำ/ตกถนนในทางโค้ง":"Overturned/ran off road on a curve","รถทางตรงชนทางตรง":"Through vehicle collided with through vehicle","รถทางตรงชนรถที่กำลังกลับรถ":"Through vehicle collided with vehicle making a U-turn","รถทางตรงชนรถเลี้ยวขวา":"Through vehicle collided with right-turning vehicle","รถทางตรงชนรถเลี้ยวซ้าย":"Through vehicle collided with left-turning vehicle","รถเลี้ยวขวาชนกับรถทางตรงหรือเลี้ยวขวา":"Right-turning vehicle collided with through/right-turning vehicle","รถเลี้ยวขวาชนรถทางตรง":"Right-turning vehicle collided with through vehicle","รถเลี้ยวขวาชนรถเลี้ยวขวา":"Right-turning vehicles collided","รถเลี้ยวขวาชนรถเลี้ยวซ้าย":"Right-turning vehicle collided with left-turning vehicle","รถเลี้ยวซ้ายชนรถทางตรง":"Left-turning vehicle collided with through vehicle","อื่นๆ":"Other","เฉี่ยวชนรถข้างเคียง (ช่องจราจรคู่ขนานกัน)":"Sideswipe collision with adjacent vehicle (parallel lanes)","เลี้ยว/ถอยชน":"Collision while turning/reversing","เลี้ยว/ถอยชนชนเข้าข้างหลัง":"Collision while turning/reversing; struck the rear","เสียการควบคุม":"Loss of control","เสียการควบคุมในทางโค้ง":"Loss of control on a curve","เสียหลัก ตกถนนขวา":"Lost control and ran off road to the right","เสียหลัก ตกถนนชนวัตถุทางขวา":"Lost control, ran off road, and struck an object on the right","เสียหลัก ตกถนนชนวัตถุทางซ้าย":"Lost control, ran off road, and struck an object on the left","เสียหลัก ตกถนนทางซ้าย":"Lost control and ran off road to the left","เสียหลัก ตกถนนโค้งขวา":"Lost control and ran off road on a right curve","เสียหลัก ตกถนนโค้งขวา/ชนสิ่งของ":"Lost control and ran off road on a right curve/struck an object","เสียหลัก ตกถนนโค้งซ้าย":"Lost control and ran off road on a left curve","เสียหลัก ตกถนนโค้งซ้าย/ชนสิ่งของ":"Lost control and ran off road on a left curve/struck an object","เสียหลักแล้วรถปีนข้ามเกาะกลาง":"Lost control and mounted/crossed the median","แซงขวาชนกับรถเลี้ยวขวา":"Overtaking on the right and collided with a right-turning vehicle","แซงไม่พ้น หักชนรถที่ถูกแซง":"Unable to complete overtaking and swerved into the overtaken vehicle","ไม่มีรายละเอียด":"No details"
}

OTHER_DETAILS = {
 "ชนเสาไฟฟ้าสองสว่างด้านขวาทาง":"struck a lighting pole on the right side of the road","กระโปรงเข้าซี่ล้อรถจักรยานยนต์":"garment caught in motorcycle wheel spokes","ขับขี่รถจักรยานยนต์ล้มเอง":"motorcycle rider fell without collision","ขับขี่ล้มเอง":"fell without collision while riding","ขับรถจักรยายนต์เร็ว":"motorcycle speeding","ขับรถชนที่กั้นข้างถนนทางด้านซ้ายทาง":"vehicle struck the roadside barrier on the left","ขับรถตัดหน้ารถกระชั้นชิด":"vehicle suddenly cut in front of another vehicle","ขับรถเร็วเกินกำหนด":"speeding","ขับรถเสียหลักล้มเอง":"lost control and fell without collision","จักรยานยนต์ล้มเอง":"motorcycle fell without collision","จักรยานยนต์แฉลบล้มเอง":"motorcycle glanced off and fell without collision","ชนกล้องวงจรปิดที่ติดที่ติดพื้นทางลอด":"struck a CCTV camera installed on the underpass surface","ชนกับกระบือ":"collided with a buffalo","ชนกับรถอีกคันหนึ่ง":"collided with another vehicle","ชนกับแบริเออร์":"struck a barrier","ชนขณะรถอีกครั้งวิ่งกินเลนขวา":"collision when another vehicle encroached into the right lane","ชนด้านข้าง":"side collision","ชนตัดหน้ากระชั้นชิด":"sudden cut-in collision","ชนทางเท้า":"struck the sidewalk","ชนที่ัพักอาศัย":"struck a residence","ชนท้ายรถจักรยานยนตื":"rear-ended a motorcycle","ชนท้ายรถที่จอดข้างทาง":"rear-ended a vehicle parked roadside","ชนประสาน":"head-on collision","ชนป้ายOverhang":"struck an overhang sign","ชนรถที่จอดอยู่":"struck a parked vehicle","ชนราวกันตกคอนกรีต":"struck a concrete guardrail","ชนสัตว์":"animal collision","ชนสุนัก":"struck a dog","ชนสุนัข":"struck a dog","ชนเสาบ้านข้างทาง":"struck a roadside house post","ชนเสาหลักกันโค้ง":"struck a curve delineator post","ชนแบริเออร์และสัญญาณไฟกระพริบ":"struck a barrier and flashing signal","ดื่มแล้วขับ":"drunk driving","ตัดหน้ากระชั้นชิด":"sudden cut-in","ตัดหน้ารถยนตร์":"cut in front of a car","พลิกคว่ำ":"overturned","รถกะบะเชียวชนรถการเกษตรบริเวณทางโค้ง":"pickup sideswiped a farm vehicle on a curve","รถจักรยานยนต์เฉี่ยวชนรถจักรยานยนต์  ย้อนสร":"motorcycle sideswiped a motorcycle traveling against traffic","รถจักรยามยนต์ข้ามเลน":"motorcycle crossed lanes","รถชนคอสะพาน":"vehicle struck a bridge abutment","รถทางตรงชนรถสวนเลน":"through vehicle collided with an oncoming vehicle","รถบรรทุกถอยมาชนรถจักรยานยนต์":"truck reversed into a motorcycle","รถระบะหลุดโค้งชนกับรถพ่วง 18ล้อ":"pickup left the curve and collided with an 18-wheel trailer truck","ระบุ":"specified","ล้มเอง (ถนนกำลังก่อสร้าง)":"fell without collision (road under construction)","ล้มเอง":"fell without collision","ล้อรถหลุด ขณะโค้ง":"wheel detached while cornering","สิ่งของตกหล่น":"fallen object","สุนัขตัดหน้ากระชั้นชิด":"dog suddenly cut in front","หลบด่าน ชรบ.":"evaded a village security checkpoint","หลุดโค้ง":"ran off a curve","เฉี่ยวชน":"sideswipe collision","เฉี่ยวชนกัน":"sideswipe collision","เพลิงไหม้":"fire","เสียการควบคุมไปชนกันกับแบริเออร์":"lost control and struck a barrier","เสียหลัก ล้ำช่องทางจราจร":"lost control and encroached into another lane","เสียหลักขับลงข้างทาง":"lost control and drove off the roadside","เสียหลักพลิกควำล้มเอง":"lost control, overturned, and fell without collision","เสียหลักพลิกคว่ำ":"lost control and overturned","เสียหลักพลิกคว่ำหรือล้มเอง":"lost control and overturned or fell without collision","เสียหลักพลิกควํ่า":"lost control and overturned","เสียหลักรื่่นไถลเข้ามาในช่องทางเดินรถตรงข้าม":"lost control and slid into the opposing lane","เสียหลักล้มเอง":"lost control and fell without collision","แฉลบล้มเอง":"glanced off and fell without collision"
}
OTHER_NO_PARENS = {
 "อื่นๆก้มรับโทรศัพท์":"Other: bent down to pick up a phone","อื่นๆจยย.ย้อนศรเฉี่ยวชน":"Other: motorcycle traveling against traffic sideswiped another vehicle","อื่นๆชนก้างปลา":"Other: struck a gore marker","อื่นๆชนก้างปลาทางลง":"Other: struck a gore marker at an exit ramp","อื่นๆชนประสานงา":"Other: head-on collision","อื่นๆชนป้ายจำกัดความสูง":"Other: struck a height-limit sign","อื่นๆชนป้ายอีซีพาส":"Other: struck an Easy Pass sign","อื่นๆชนป้ายเตือนหน้าตู้":"Other: struck a warning sign in front of a booth","อื่นๆชนรั้วลวดหนาม":"Other: struck a barbed-wire fence","อื่นๆชนหัวเกาะก้างปลา":"Other: struck the nose of a gore area","อื่นๆชนเสาไฟฟ้าข้างทาง":"Other: struck a roadside utility pole","อื่นๆชนแบริเออร์":"Other: struck a barrier","อื่นๆชนแบริเออร์น้ำ":"Other: struck a water-filled barrier","อื่นๆตกข้างทาง":"Other: ran off the roadside","อื่นๆถอยชนเสาไฟส่องสว่าง":"Other: reversed into a lighting pole","อื่นๆถอยหลังชน":"Other: reversing collision","อื่นๆพลิกตะแคง":"Other: tipped onto its side","อื่นๆรถกระบะชนรถนั่งบุคคล":"Other: pickup collided with a passenger car","อื่นๆรถเกิดเพลิงไหม้":"Other: vehicle fire","อื่นๆหางพ่วงหลุด":"Other: trailer detached","อื่นๆเฉี่ยวก้างปลา":"Other: sideswiped a gore marker","อื่นๆเฉี่ยวชนแท่งปูน":"Other: sideswiped a concrete block","อื่นๆเฉี่ยวชนแบริเออร์":"Other: sideswiped a barrier","อื่นๆเฉี่ยวชนแล้วพลิกคว่ำ":"Other: sideswiped and overturned","อื่นๆเบรคกระชั้นชิด":"Other: sudden braking"
}

THAI = re.compile(r"[\u0E00-\u0E7F]")

def location(value):
    if value in LOCATION_PARTS:
        return LOCATION_PARTS[value]
    for base in sorted(LOCATION_PARTS, key=len, reverse=True):
        prefix = base + "+"
        if value.startswith(prefix):
            suffix = value[len(prefix):]
            if suffix in LOCATION_PARTS:
                return LOCATION_PARTS[base] + " + " + LOCATION_PARTS[suffix]
    raise KeyError(f"Unmapped location: {value}")

def accident(value):
    if value in ACCIDENT_EXACT:
        return ACCIDENT_EXACT[value]
    if value in OTHER_NO_PARENS:
        return OTHER_NO_PARENS[value]
    m = re.fullmatch(r"อื่นๆ \((.*)\)", value)
    detail = m.group(1).strip() if m else None
    if detail in OTHER_DETAILS:
        return f"Other ({OTHER_DETAILS[detail]})"
    raise KeyError(f"Unmapped accident type: {value}")

TRANSLATORS = {
    "หน่วยงาน": lambda x: AGENCY[x], "สายทางหน่วยงาน": lambda x: ROAD_TYPE[x],
    "จังหวัด": lambda x: PROVINCES[x], "รถคันที่ 1": lambda x: VEHICLE[x], "รถคันที่1": lambda x: VEHICLE[x],
    "สภาพอากาศ": lambda x: WEATHER[x], "บริเวณที่เกิดเหตุ": location,
    "บริเวณที่เกิดเหตุ/ลักษณะทาง": location, "มูลเหตุสันนิษฐาน": lambda x: CAUSE[x],
    "ลักษณะการเกิดเหตุ": accident, "ลักษณะการเกิดอุบัติเหตุ": accident,
}

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def translate_file(year):
    src = RAW / f"accident{year}.csv"
    dst = OUT / f"accident{year}_en.csv"
    rows = 0
    with src.open(encoding="utf-8-sig", newline="") as fi, dst.open("w", encoding="utf-8-sig", newline="") as fo:
        reader = csv.DictReader(fi)
        original_headers = reader.fieldnames
        if not original_headers or any(h not in HEADERS and h not in {"ACC_CODE", "LATITUDE", "LONGITUDE"} for h in original_headers):
            raise ValueError(f"Unexpected header in {src.name}")
        output_headers = [HEADERS.get(h, h) for h in original_headers]
        writer = csv.writer(fo)
        writer.writerow(output_headers)
        for row in reader:
            out = []
            for h in original_headers:
                value = row[h]
                if value and h in TRANSLATORS:
                    value = TRANSLATORS[h](value.strip())
                    if THAI.search(value):
                        raise ValueError(f"Thai remains in translated {h}: {value}")
                out.append(value)
            writer.writerow(out)
            rows += 1
    return {"year": year, "rows": rows, "columns": len(original_headers), "source_sha256": sha(src), "output_sha256": sha(dst), "output_bytes": dst.stat().st_size}

def validate(year, report):
    src = RAW / f"accident{year}.csv"
    dst = OUT / f"accident{year}_en.csv"
    protected = {"ปีที่เกิดเหตุ","วันที่เกิดเหตุ","เวลา","วันที่รายงาน","เวลาที่รายงาน","ACC_CODE","รหัสสายทาง","สายทาง","ก.ม.","KM","จำนวนรถที่เกิดเหตุ (รวมคันที่ 1)","จำนวนผู้เสียชีวิต","รวมจำนวนผู้บาดเจ็บ","LATITUDE","LONGITUDE","รถที่เกิดเหตุ","รถและคนที่เกิดเหตุ","รถจักรยานยนต์","รถสามล้อเครื่อง","รถยนต์นั่งส่วนบุคคล","รถตู้","รถปิคอัพโดยสาร","รถโดยสารมากกว่า4ล้อ","รถปิคอัพบรรทุก4ล้อ","รถบรรทุก6ล้อ","รถบรรทุกไม่เกิน10ล้อ","รถบรรทุกมากกว่า10ล้อ","รถอีแต๋น","รถอื่นๆ","คนเดินเท้า","ผู้เสียชีวิต","ผู้บาดเจ็บสาหัส","ผู้บาดเจ็บเล็กน้อย"}
    with src.open(encoding="utf-8-sig", newline="") as a, dst.open(encoding="utf-8-sig", newline="") as b:
        ra, rb = csv.reader(a), csv.reader(b)
        ha, hb = next(ra), next(rb)
        if hb != [HEADERS.get(h, h) for h in ha]: raise AssertionError("Header mismatch")
        indexes = [i for i,h in enumerate(ha) if h in protected]
        count = 0
        for count, (x, y) in enumerate(zip(ra, rb), 1):
            if len(x) != len(y): raise AssertionError(f"Column mismatch row {count}")
            if any(x[i] != y[i] for i in indexes): raise AssertionError(f"Protected value changed row {count}")
        if count != report["rows"]: raise AssertionError("Row-count mismatch")
    report["validated"] = True

def main():
    reports = []
    for year in range(2019, 2026):
        report = translate_file(year)
        validate(year, report)
        reports.append(report)
    manifest = OUT / "translation_manifest.json"
    manifest.write_text(json.dumps({"scope":"Thailand road-accident datasets, 2019–2025","encoding":"UTF-8 with BOM","policy":"English headers and standardized categorical values translated. Proper road names and route codes retained verbatim to protect official identifiers. Dates, times, IDs, numeric values, coordinates, row order, and source files are unchanged.","files":reports}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(reports, indent=2))

if __name__ == "__main__":
    main()
