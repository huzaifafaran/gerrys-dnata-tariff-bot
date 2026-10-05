from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
from connector.cnxn import server_access
from math import ceil
from datetime import datetime


# Create your views here.
def index(request):
    return render(request, 'form.html')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def cargo_class_parser(cargo_class):
    # For ICG
    if cargo_class == 'IDT (DR)':
        cargo_class = 'IDT'

    elif cargo_class == 'RAD (RAM)':
        cargo_class = 'RAD'

    elif cargo_class == 'DGR/AVI':
        cargo_class = 'DGR'

    # For Pharma
    elif cargo_class == 'GEN (PIL)':
        cargo_class = 'GEN'

    elif cargo_class == 'DGR (PDG)':
        cargo_class = 'DGR'

    elif cargo_class == '15 to 25 Degree Celsius (IRT)' or cargo_class == '15 to 25 Degree Celsius (PRT)' or cargo_class == '15 to 25 Degree Celsius (CRT)':
        cargo_class = '15 to 25 Degree Celsius'

    elif cargo_class == '2 to 8 Degree Celsius (ICO)' or cargo_class == '2 to 8 Degree Celsius (COL)' or cargo_class == '2 to 8 Degree Celsius (PIC)':
        cargo_class = '2 to 8 Degree Celsius'

    elif cargo_class == 'Freezer (IRO)' or cargo_class == 'Freezer (PRF)' or cargo_class == 'Freezer (FRO)':
        cargo_class = 'Freezer'

    else:
        cargo_class = cargo_class

    return cargo_class

def calculate_tariff(request):

    # AWB = request.POST["AWB"]
    # HAWB = request.POST["HAWB"]
    arrival_date = request.POST["arrival_date"]
    payment_date = request.POST["payment_date"]
    category = request.POST["category"]
    actual_cargo_class = request.POST["cargo_class"]
    weight = request.POST["weight"]
    station = request.POST["Station"]

    cargo_class = cargo_class_parser(actual_cargo_class)

    calculations_sql = '''

    DECLARE @Arrival_Date date 
    DECLARE @Payment_Date date 
    DECLARE @Category nvarchar(50) 
    DECLARE @Cargo_Class nvarchar(50) 
    DECLARE @Weight float 
    DECLARE @Station nvarchar(50)


    SET @Arrival_Date = '{}';
    SET @Payment_Date = '{}';
    SET @Category = '{}';
    SET @Cargo_Class = '{}';
    SET @Weight = {};
    SET @Station = '{}'

    SELECT t.*
    ,tax.Tax_Rate
	,ISNULL(ov.Charges_PKR,0) Oversized_Charges 
    ,ISNULL(doc.Charges_D_Console,0) AS [Deconsole Charges]
    ,0 AS [DO Fee]
    ,ISNULL(doc.Charges_Doc,0) [Documentation Charges]
    ,ISNULL(CASE WHEN hd.Charges_Per = 'Per KG' THEN hd.Charges_PKR * Weight ELSE hd.Charges_PKR END,0) AS [Handling]
    ,ISNULL(CASE WHEN gd.Charges_Per = 'Per Day' THEN (Dwell_Time - FLOOR(gd.Free_Days)) * gd.Charges_PKR ELSE 
    (Dwell_Time - FLOOR(gd.Free_Days)) * gd.Charges_PKR * Weight END,0) as [Storage]
    ,CEILING((ISNULL(doc.Charges_D_Console,0)) + 
     (ISNULL(doc.Charges_Doc,0)) +
     (ISNULL(CASE WHEN hd.Charges_Per = 'Per KG' THEN hd.Charges_PKR * Weight ELSE hd.Charges_PKR END,0)) +
     (ISNULL(CASE WHEN gd.Charges_Per = 'Per Day' THEN (Dwell_Time - FLOOR(gd.Free_Days)) * gd.Charges_PKR ELSE 
    (Dwell_Time - FLOOR(gd.Free_Days)) * gd.Charges_PKR * Weight END,0)) + ISNULL(ov.Charges_PKR,0)) Total

    FROM (
    SELECT 
    		 @Arrival_Date Arrival_Date
    		,@Payment_Date Payment_Date
    		,@Category Category
    		,@Cargo_Class Cargo_Class
    		,@Weight [Weight]
            ,@Station [Station]
    		,DATEDIFF(day, @Arrival_Date, @Payment_Date) + 1 [Dwell_Time]
    		) t
    		LEFT JOIN [dbo].[Tariff_Handling] hd
    		ON  hd.Cargo_Class = t.Cargo_Class
    		AND hd.Category = t.Category 
    		AND ROUND(t.Weight,0) >= hd.Wt_Min
    		AND ROUND(t.Weight,0) <= hd.Wt_Max
    		AND CONVERT(DATE, Payment_Date) >= hd.Effective_Date
    		AND CONVERT(DATE, Payment_Date) <= hd.[Expiry_Date]


    		LEFT JOIN [dbo].[Tariff_Godown] gd ON
    		gd.Cargo_Class = t.Cargo_Class
    		AND gd.Category = t.Category
    		AND ROUND(t.Weight ,0) >= gd.Wt_Min
    		AND ROUND(t.Weight ,0) <= gd.Wt_Max
    		AND ROUND(t.Dwell_Time,2) >= gd.Dwell_Min
    		AND ROUND(t.Dwell_Time,2) <= gd.Dwell_Max
    		AND CONVERT(DATE, Payment_Date) >= gd.Effective_Date
    		AND CONVERT(DATE, Payment_Date) <= gd.[Expiry_Date]
    

    		LEFT JOIN [dbo].[Tariff_Doc] doc ON
    		doc.Category = t.Category
    		AND CONVERT(DATE, Payment_Date) >= doc.Effective_Date
    		AND CONVERT(DATE, Payment_Date) <= doc.[Expiry_Date]

            LEFT JOIN [dbo].Tariff_Oversized ov ON
    		ov.Category = t.Category
    		AND CONVERT(DATE, Payment_Date) >= ov.Effective_Date
    		AND CONVERT(DATE, Payment_Date) <= ov.[Expiry_Date]
			AND ROUND(t.Weight ,0) >= ov.Wt_Min
    		AND ROUND(t.Weight ,0) <= ov.Wt_Max

            LEFT JOIN [dbo].[Tariff_Tax] tax ON
    		tax.Station = t.Station
    		AND CONVERT(DATE, Payment_Date) >= tax.Effective_Date
    		AND CONVERT(DATE, Payment_Date) <= tax.[Expiry_Date]

    
    
    '''.format(arrival_date, payment_date, category, cargo_class, weight, station)

    ip = get_client_ip(request)

    cnxn = server_access()
    df = pd.read_sql(calculations_sql, cnxn)
    # dwell_time = round(df['Dwell_Time'].values[0],2)
    # deconsole = round(df['Deconsole Charges'].values[0],2)
    # do = round(df['DO Fee'].values[0],2)
    # handling = round(df['Handling'].values[0],2)
    # storage = round(df['Storage'].values[0],2)
    # total = round(df['Total'].values[0],0)
    dwell_time = ceil(df['Dwell_Time'].values[0])
    deconsole = ceil(df['Deconsole Charges'].values[0])
    do = ceil(df['DO Fee'].values[0])
    doc_charges = ceil(df['Documentation Charges'].values[0])
    handling = ceil(df['Handling'].values[0])
    storage = ceil(df['Storage'].values[0])
    # oversize = ceil(df['Oversized_Charges'].values[0])
    tax_rate = (df['Tax_Rate'].values[0])/100
    total = deconsole + doc_charges + handling + storage # oversize
    # total = ceil(df['Total'].values[0])
    tax = round(tax_rate * total)
    grand_total = total + tax
    

    # populate log file
    f = open("log.txt", "a")
    f.write("{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        arrival_date, payment_date, \
        category, cargo_class, weight, 
        dwell_time, deconsole, 
        doc_charges, handling, 
        storage, tax, grand_total,station,ip))
    f.close()

    dwell_time = f"{dwell_time:,}"
    deconsole = f"{deconsole:,}"
    do = f"{do:,}"
    doc_charges = f"{doc_charges:,}"
    handling = f"{handling:,}"
    storage = f"{storage:,}"
    # oversize = f"{oversize:,}"
    tax = f"{tax:,}"
    total = f"{grand_total:,}"

    return render(request, 'calculations.html', {'arrival_date':arrival_date, 
    'payment_date':payment_date, 'category':category, 'cargo_class':cargo_class, 'weight':weight,
    'dwell_time':dwell_time, 'deconsole':deconsole, 'doc_charges':doc_charges, 'handling':handling, 
    'storage':storage, 'tax':tax, 'total':total})