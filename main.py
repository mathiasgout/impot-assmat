import os
import re
from io import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from constants import *

 
class ImpotAssmat:

    MAIN_PATH = os.path.dirname(os.path.realpath(__file__))
    PDF_FOLDER_PATH = os.path.join(MAIN_PATH, NOM_DOSSIER_PDF)

    def __init__(self):

        self.parse_pdf()
        self.save_results()

    def parse_pdf(self):
        """ Parse PDF and extract infos """

        self.result_dict = dict()

        for pdf in os.listdir(self.PDF_FOLDER_PATH):

            # PDF parsing
            resouce_manager = PDFResourceManager()
            retstr = StringIO()
            device = TextConverter(resouce_manager, retstr, laparams=LAParams(char_margin=50))

            with open(os.path.join(self.PDF_FOLDER_PATH, pdf), "rb") as f: 
                interpreter = PDFPageInterpreter(resouce_manager, device)
                for page in PDFPage.get_pages(f, check_extractable=True):
                    interpreter.process_page(page)
                text = retstr.getvalue()

            # Text cleaning
            text = text.lower()
            text = text.replace("\n \n", "\n")
            text_list = re.split(r'\n{1,}', text)

            # Info extraction
            for i, item in enumerate(text_list):
                text_list[i] = re.compile(r"\s+").sub(" ", item).strip()
                
                if "nombre d'heures normales" in text_list[i]:
                    jour = float(text_list[i].split()[3].replace(",", "."))/8
                elif "référence employeur" in text_list[i]:
                    employeur = text_list[i+1].upper() 
                elif "csg + rds non deductible de l'impot sur le revenu" in text_list[i]:
                    csg = float(text_list[i].split()[12].replace(",", "."))
                elif "salaire net déclaré (y compris indemnités)" in text_list[i]:
                    salaire_net = float(text_list[i].split()[6].replace(",", "."))

            if employeur not in self.result_dict:
                self.result_dict[employeur] = dict()
                self.result_dict[employeur]["jour_tot"] = jour
                self.result_dict[employeur]["csg_tot"] = csg
                self.result_dict[employeur]["salaire_net_tot"] = salaire_net
            else:
                self.result_dict[employeur]["jour_tot"] += jour
                self.result_dict[employeur]["csg_tot"] += csg
                self.result_dict[employeur]["salaire_net_tot"] += salaire_net
    
    def save_results(self):
        """ Save results in resultats.txt """
        
        with open(os.path.join(self.MAIN_PATH, "resultats.txt"), "w") as f:
            salaire_tot = 0
            for employeur in self.result_dict:
                salaire_employeur_tot = round(self.result_dict[employeur]["salaire_net_tot"] + self.result_dict[employeur]["csg_tot"] - 
                                              self.result_dict[employeur]["jour_tot"]*3*SMIC, 2)
                f.write("{} : {} €\n".format(employeur, salaire_employeur_tot))
                salaire_tot += salaire_employeur_tot
            
            f.write("\n\n")
            f.write("TOTAL ANNÉE: {} €".format(round(salaire_tot, 2)))
            

if __name__ == "__main__":
    ImpotAssmat()