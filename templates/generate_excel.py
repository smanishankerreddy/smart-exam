from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Sheet1"
ws.append(["Question", "A", "B", "C", "D", "Answer"])  # headers
ws.append(["Capital of India?", "Mumbai", "Delhi", "Kolkata", "Chennai", "B"])
ws.append(["5 + 2 = ?", "5", "6", "7", "8", "C"])
ws.append(["Sun rises in?", "West", "East", "North", "South", "B"])

wb.save("questions.xlsx")
