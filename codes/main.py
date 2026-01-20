import os
from data_augmentation import augment_adl


# This is the input format used to modify a line in an ADL file.
input_data = {
            "object": [
                        {
                            "name": "jets", 
                            "attr": {
                                        "pT(Jet)": {">=": (10, 20)},
                                        "abs(Eta(Jet))": {"<": (2.3, 2.4)}
                                    }
                        },
                        {
                            "name": "vetomuons",
                            "attr": {
                                        "pT(Muon)": {"<": (10, 20)}
                                    }
                        },
                        {
                            "name": "vetoelectrons",
                            "attr": {
                                        "pT(Electron)": {"<": (10, 20)}
                                    }
                        },
                        {
                            "name": "hadisotracks",
                            "attr": {
                                        ("abs(pdgID(Trk))", "abs(pdgID(Trk))"): ({("==",): (11, 12)}, {("==",): (13,)})
                                    }
                        }
         
            ],
            "region": [

                {
                    "name": "presel",
                    "attr": {   
                                "HT": {">": (250, 275, )},
                                "MHT / HT": {("<=", ">"): (1,)} ,
                                "size(muisotracks)": {"==": (0, 1, 2, 3)}
                            }
                }
            ]
        }


cwd = os.getcwd()
file_path = cwd + "/Sample_Datasets/CMS-SUS-19-006_CutLang.adl.txt"

lines = augment_adl(file_path, input_data)