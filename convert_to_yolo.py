import os
import xml.etree.ElementTree as ET
import shutil
from pathlib import Path

# Configuration
classes = ["cheeseburger_475cal", "fries_350cal"]
input_dirs = {
    "train": "images/train",
    "val": "images/test"  # Using 'test' as 'val' for YOLO
}
output_root = "yolo_dataset"

def convert_box(size, box):
    dw = 1. / size[0]
    dh = 1. / size[1]
    x = (box[0] + box[1]) / 2.0
    y = (box[2] + box[3]) / 2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x * dw
    w = w * dw
    y = y * dh
    h = h * dh
    return (x, y, w, h)

def convert_xml_to_yolo():
    os.makedirs(output_root, exist_ok=True)
    
    for split, input_path in input_dirs.items():
        img_out = Path(output_root) / "images" / split
        lbl_out = Path(output_root) / "labels" / split
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)
        
        print(f"Processing {split}...")
        
        files = os.listdir(input_path)
        for f in files:
            if f.endswith(".xml"):
                xml_path = os.path.join(input_path, f)
                tree = ET.parse(xml_path)
                root = tree.getroot()
                size = root.find("size")
                w = int(size.find("width").text)
                h = int(size.find("height").text)
                
                # YOLO label file
                label_file = lbl_out / f.replace(".xml", ".txt")
                
                with open(label_file, "w") as out_file:
                    for obj in root.iter("object"):
                        cls = obj.find("name").text
                        if cls not in classes:
                            # Try to match fuzzy names if necessary, but here they seem exact
                            # Actually, let's just use the first match for food names
                            if "cheeseburger" in cls: cls = "cheeseburger_475cal"
                            if "fries" in cls: cls = "fries_350cal"
                        
                        if cls not in classes:
                            continue
                            
                        cls_id = classes.index(cls)
                        xmlbox = obj.find("bndbox")
                        b = (float(xmlbox.find("xmin").text), float(xmlbox.find("xmax").text), 
                             float(xmlbox.find("ymin").text), float(xmlbox.find("ymax").text))
                        bb = convert_box((w, h), b)
                        out_file.write(str(cls_id) + " " + " ".join([str(a) for a in bb]) + "\n")
                
                # Copy image
                img_name = f.replace(".xml", ".jpg")
                src_img = os.path.join(input_path, img_name)
                if os.path.exists(src_img):
                    shutil.copy(src_img, img_out / img_name)

    # Create data.yaml
    yaml_content = f"""
path: ./yolo_dataset
train: images/train
val: images/val

names:
  0: cheeseburger_475cal
  1: fries_350cal
"""
    with open("data.yaml", "w") as f:
        f.write(yaml_content.strip())
    print("Done! data.yaml created.")

if __name__ == "__main__":
    convert_xml_to_yolo()
