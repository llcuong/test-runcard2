from django.shortcuts import render
from thickness_device.database import mes_database, vnedc_database
from django.shortcuts import redirect
import barcode
import base64
from datetime import datetime, timedelta
from io import BytesIO
from barcode.writer import SVGWriter
barcode.base.Barcode.default_writer_options['write_text'] = False
db_mes = mes_database()
barcode_class = barcode.get_barcode_class('code128')

def barcodepage(request):
    try:
        period_times = ['6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17',
                        '18', '19', '20', '21', '22', '23', '0', '1', '2', '3', '4', '5']

        now = datetime.now() + timedelta(minutes=39)# + timedelta(hours=18)# - timedelta(hours=8) #46 21
        # print('barcode time: ', now)
        # now = datetime.strptime('2024-11-22 05:15:00.00000', '%Y-%m-%d %H:%M:%S.%f') + timedelta(minutes=39)
        fnow = f"{int((str(now).split(' ')[-1]).split(':')[0])} giờ, ngày {datetime.strptime(str(now).split(' ')[0], '%Y-%m-%d').strftime('%d-%m-%Y')}"
        current_mins = int(now.strftime('%M'))
        current_time = int(now.strftime('%H'))
        current_date = now  #datetime.strptime(date_string, "%Y-%m-%d")
        if current_time > 5:
            data_date1 = current_date.strftime('%Y-%m-%d')
            data_date2 = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
            current_date = data_date1
        else:
            data_date1 = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
            data_date2 = current_date.strftime('%Y-%m-%d')
            current_date = data_date2
        yesterday = str((datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d'))
        plant = str(request.GET.get('plant', '')).upper()
        mach = request.GET.get('mach', '')
        time = request.GET.get('time', '')


        line = request.GET.get('line', '')
        wo = int(request.GET.get('wo', '0'))
        # print('plant: ', plant)
        # print('mach: ', mach)
        tomorrow = str((datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d'))

        port = request.META.get('SERVER_PORT')
        if port == '10000':
            if not any([plant, mach, time, line]):
                plant, mach, current_date, time, line = 'NBR', 'VN_GD_NBR1_L01', current_date, current_time, 'A1'
                return redirect(f'/?plant={plant}&mach={mach}&date={current_date}&time={time}&line={line}&wo=0')
        if port == '10001':
            if not any([plant, mach, time, line]):
                plant, mach, current_date, time, line = 'PVC', 'VN_GD_PVC1_L01', current_date, current_time, 'A1'
                return redirect(f'/?plant={plant}&mach={mach}&date={current_date}&time={time}&line={line}&wo=0')
        if current_time > 5:
            if int(time) > current_time or int(time) < 6:
                time = str(current_time)
        if current_time < 6:
            if 0 <= int(time) <= 5 and int(time) > current_time:
                time = str(current_time)
        sql01 = f"""SELECT id as mach_id, name as machine_name
                    FROM [PMGMES].[dbo].[PMG_DML_DataModelList]
                    WHERE DataModelTypeId = 'DMT000003'
                    and Abbreviation like '%{plant}%'
                    order by machine_name"""
        machine_lines_dicts = db_mes.select_sql_dict(sql01)

        if plant == 'PVC':
            machine_lines_name = [machine_lines_dict['machine_name'] for machine_lines_dict in machine_lines_dicts][:12]
        else:
            machine_lines_name = [machine_lines_dict['machine_name'] for machine_lines_dict in machine_lines_dicts]
        machine_lines_short = [str(machine_lines_dict['machine_name']).split('_')[-1] for machine_lines_dict in machine_lines_dicts]
        machine_lines = zip(machine_lines_name, machine_lines_short)

        nbr_lines = ['A1', 'B1', 'A2', 'B2']
        pvc_lines = ['', 'A1', 'B1', '']


        sql02 = f"""SELECT rc.id, rc.WorkOrderId, wo.PartNo, wo.CustomerCode, wo.CustomerName, wo.ProductItem, wo.AQL,
                    MAX(CASE WHEN ir.OptionName = 'Roll' THEN ir.InspectionValue END) AS Roll,
                    MAX(CASE WHEN ir.OptionName = 'Cuff' THEN ir.InspectionValue END) AS Cuff,
                    MAX(CASE WHEN ir.OptionName = 'Palm' THEN ir.InspectionValue END) AS Palm,
                    MAX(CASE WHEN ir.OptionName = 'Finger' THEN ir.InspectionValue END) AS Finger,
                    MAX(CASE WHEN ir.OptionName = 'FingerTip' THEN ir.InspectionValue END) AS FingerTip,
                    MAX(CASE WHEN ir.OptionName = 'Weight' THEN ir.InspectionValue END) AS Weight,
                    MAX(CASE WHEN ir.OptionName = 'Tensile' THEN ir.InspectionValue END) AS Tensile,
                    MAX(CASE WHEN ir.OptionName = 'Elongation' THEN ir.InspectionValue END) AS Elongation, 
                    au.Name
                    FROM [PMGMES].[dbo].[PMG_MES_RunCard] rc
                    join [PMGMES].[dbo].[PMG_MES_WorkOrder] wo
                    on wo.id = rc.WorkOrderId
                    left join [PMGMES].[dbo].[PMG_MES_IPQCInspectingRecord] ir
                    on ir.RunCardId = rc.id
                    join [PMGMES].[dbo].[AbpUsers] au
                    on rc.CreatorUserId = au.Id
                    WHERE rc.MachineName = '{mach}'
                        AND rc.WorkCenterTypeName = '{plant}'
                        AND rc.LineName = '{line}'
                        AND ((rc.Period > 5 AND rc.InspectionDate = '{data_date1}')
                            OR (rc.Period <= 5 AND rc.InspectionDate = '{data_date2}'))
                    AND rc.Period = '{time}'
                    AND wo.StartDate is not NULL
                    Group by rc.id, rc.WorkOrderId, wo.PartNo, wo.CustomerCode, wo.CustomerName, wo.ProductItem, wo.AQL, au.Name"""
        text_to_convert_dict = db_mes.select_sql_dict(sql02)
        wo_len = len(text_to_convert_dict)
        if wo_len > 0:
            if wo_len == 1:
                wo = 0
            wo_list = [text_to_convert['WorkOrderId'] for text_to_convert in text_to_convert_dict]
            wo_id = [str(number) for number in range(wo_len)]
            wo_zip = zip(wo_list, wo_id)
            mavattu = text_to_convert_dict[wo]['PartNo']
            makhachhang = text_to_convert_dict[wo]['CustomerCode']
            tenkhachhang = text_to_convert_dict[wo]['CustomerName']
            aql = text_to_convert_dict[wo]['AQL']
            congdon = text_to_convert_dict[wo]['WorkOrderId']
            loai = text_to_convert_dict[wo]['ProductItem']
            may = f"{plant}{mach.split('_')[-1][1:]}"
            roll = text_to_convert_dict[wo]['Roll'] if text_to_convert_dict[wo]['Roll'] is not None else ''
            cuff = text_to_convert_dict[wo]['Cuff'] if text_to_convert_dict[wo]['Cuff'] is not None else ''
            palm = text_to_convert_dict[wo]['Palm'] if text_to_convert_dict[wo]['Palm'] is not None else ''
            finger = text_to_convert_dict[wo]['Finger'] if text_to_convert_dict[wo]['Finger'] is not None else ''
            fingerTip = text_to_convert_dict[wo]['FingerTip'] if text_to_convert_dict[wo]['FingerTip'] is not None else ''
            weight = str(round(float(text_to_convert_dict[wo]['Weight']), 3)) if text_to_convert_dict[wo]['Weight'] is not None else ''
            tensile = str(round(float(text_to_convert_dict[wo]['Tensile']), 1)) if text_to_convert_dict[wo]['Tensile'] is not None else ''
            elongation = str(int(text_to_convert_dict[wo]['Elongation'])) if text_to_convert_dict[wo]['Elongation'] is not None else ''
            nguoikiemtra = text_to_convert_dict[wo]['Name']
            kichco = extract_kichco(loai)
            text_to_convert = text_to_convert_dict[wo]['id']
        else:
            wo_zip = zip('0', '0')
            text_to_convert = ' '
        barcode_svg = barcode_class(text_to_convert, writer=SVGWriter())
        buffer = BytesIO()
        barcode_svg.write(buffer)
        svg_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(e)
        pass

    return render(request, 'runcard/barcode.html', locals())

def barcodepage2(request):
    try:
        period_times = ['6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17',
                        '18', '19', '20', '21', '22', '23', '0', '1', '2', '3', '4', '5']

        date_now = str((datetime.now() + timedelta(minutes=39) - timedelta(hours=5)).date()) # - timedelta(hours=8) #46 21

        # print('barcode time: ', now)
        now = datetime.strptime(f'{date_now} 05:15:00.00000', '%Y-%m-%d %H:%M:%S.%f')
        fnow = f"{int((str(now).split(' ')[-1]).split(':')[0])} giờ, ngày {datetime.strptime(str(now).split(' ')[0], '%Y-%m-%d').strftime('%d-%m-%Y')}"
        current_mins = int(now.strftime('%M'))
        current_time = int(now.strftime('%H'))
        current_date = now  #datetime.strptime(date_string, "%Y-%m-%d")
        if current_time > 5:
            data_date1 = current_date.strftime('%Y-%m-%d')
            data_date2 = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
            current_date = data_date1
        else:
            data_date1 = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
            data_date2 = current_date.strftime('%Y-%m-%d')
            current_date = data_date2

        plant = str(request.GET.get('plant', '')).upper()
        mach = request.GET.get('mach', '')
        time = request.GET.get('time', '')
        line = request.GET.get('line', '')
        wo = int(request.GET.get('wo', '0'))
        # print('plant: ', plant)
        # print('mach: ', mach)

        port = request.META.get('SERVER_PORT')
        if port == '10000':
            if not any([plant, mach, time, line]):
                plant, mach, current_date, time, line = 'NBR', 'VN_GD_NBR1_L01', current_date, current_time, 'A1'
                return redirect(f'/?plant={plant}&mach={mach}&date={current_date}&time={time}&line={line}&wo=0')
        if port == '10001':
            if not any([plant, mach, time, line]):
                plant, mach, current_date, time, line = 'PVC', 'VN_GD_PVC1_L01', current_date, current_time, 'A1'
                return redirect(f'/?plant={plant}&mach={mach}&date={current_date}&time={time}&line={line}&wo=0')

        sql01 = f"""SELECT id as mach_id, name as machine_name
                    FROM [PMGMES].[dbo].[PMG_DML_DataModelList]
                    WHERE DataModelTypeId = 'DMT000003'
                    and Abbreviation like '%{plant}%'
                    order by machine_name"""
        machine_lines_dicts = db_mes.select_sql_dict(sql01)

        if plant == 'PVC':
            machine_lines_name = [machine_lines_dict['machine_name'] for machine_lines_dict in machine_lines_dicts][:12]
        else:
            machine_lines_name = [machine_lines_dict['machine_name'] for machine_lines_dict in machine_lines_dicts]
        machine_lines_short = [str(machine_lines_dict['machine_name']).split('_')[-1] for machine_lines_dict in machine_lines_dicts]
        machine_lines = zip(machine_lines_name, machine_lines_short)

        nbr_lines = ['A1', 'B1', 'A2', 'B2']
        pvc_lines = ['', 'A1', 'B1', '']


        sql02 = f"""SELECT rc.id, rc.WorkOrderId, wo.PartNo, wo.CustomerCode, wo.CustomerName, wo.ProductItem, wo.AQL,
                    MAX(CASE WHEN ir.OptionName = 'Roll' THEN ir.InspectionValue END) AS Roll,
                    MAX(CASE WHEN ir.OptionName = 'Cuff' THEN ir.InspectionValue END) AS Cuff,
                    MAX(CASE WHEN ir.OptionName = 'Palm' THEN ir.InspectionValue END) AS Palm,
                    MAX(CASE WHEN ir.OptionName = 'Finger' THEN ir.InspectionValue END) AS Finger,
                    MAX(CASE WHEN ir.OptionName = 'FingerTip' THEN ir.InspectionValue END) AS FingerTip,
                    MAX(CASE WHEN ir.OptionName = 'Weight' THEN ir.InspectionValue END) AS Weight,
                    MAX(CASE WHEN ir.OptionName = 'Tensile' THEN ir.InspectionValue END) AS Tensile,
                    MAX(CASE WHEN ir.OptionName = 'Elongation' THEN ir.InspectionValue END) AS Elongation, 
                    au.Name
                    FROM [PMGMES].[dbo].[PMG_MES_RunCard] rc
                    join [PMGMES].[dbo].[PMG_MES_WorkOrder] wo
                    on wo.id = rc.WorkOrderId
                    left join [PMGMES].[dbo].[PMG_MES_IPQCInspectingRecord] ir
                    on ir.RunCardId = rc.id
                    join [PMGMES].[dbo].[AbpUsers] au
                    on rc.CreatorUserId = au.Id
                    WHERE rc.MachineName = '{mach}'
                        AND rc.WorkCenterTypeName = '{plant}'
                        AND rc.LineName = '{line}'
                        AND ((rc.Period > 5 AND rc.InspectionDate = '{data_date1}')
                            OR (rc.Period <= 5 AND rc.InspectionDate = '{data_date2}'))
                    AND rc.Period = '{time}'
                    AND wo.StartDate is not NULL
                    Group by rc.id, rc.WorkOrderId, wo.PartNo, wo.CustomerCode, wo.CustomerName, wo.ProductItem, wo.AQL, au.Name"""
        text_to_convert_dict = db_mes.select_sql_dict(sql02)
        wo_len = len(text_to_convert_dict)
        if wo_len > 0:
            if wo_len == 1:
                wo = 0
            wo_list = [text_to_convert['WorkOrderId'] for text_to_convert in text_to_convert_dict]
            wo_id = [str(number) for number in range(wo_len)]
            wo_zip = zip(wo_list, wo_id)
            mavattu = text_to_convert_dict[wo]['PartNo']
            makhachhang = text_to_convert_dict[wo]['CustomerCode']
            tenkhachhang = text_to_convert_dict[wo]['CustomerName']
            aql = text_to_convert_dict[wo]['AQL']
            congdon = text_to_convert_dict[wo]['WorkOrderId']
            loai = text_to_convert_dict[wo]['ProductItem']
            may = f"{plant}{mach.split('_')[-1][1:]}"
            roll = text_to_convert_dict[wo]['Roll'] if text_to_convert_dict[wo]['Roll'] is not None else ''
            cuff = text_to_convert_dict[wo]['Cuff'] if text_to_convert_dict[wo]['Cuff'] is not None else ''
            palm = text_to_convert_dict[wo]['Palm'] if text_to_convert_dict[wo]['Palm'] is not None else ''
            finger = text_to_convert_dict[wo]['Finger'] if text_to_convert_dict[wo]['Finger'] is not None else ''
            fingerTip = text_to_convert_dict[wo]['FingerTip'] if text_to_convert_dict[wo]['FingerTip'] is not None else ''
            weight = str(round(float(text_to_convert_dict[wo]['Weight']), 3)) if text_to_convert_dict[wo]['Weight'] is not None else ''
            tensile = str(round(float(text_to_convert_dict[wo]['Tensile']), 1)) if text_to_convert_dict[wo]['Tensile'] is not None else ''
            elongation = str(int(text_to_convert_dict[wo]['Elongation'])) if text_to_convert_dict[wo]['Elongation'] is not None else ''
            nguoikiemtra = text_to_convert_dict[wo]['Name']
            kichco = extract_kichco(loai)
            text_to_convert = text_to_convert_dict[wo]['id']
        else:
            wo_zip = zip('0', '0')
            text_to_convert = ' '
        barcode_svg = barcode_class(text_to_convert, writer=SVGWriter())
        buffer = BytesIO()
        barcode_svg.write(buffer)
        svg_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(e)
        pass

    return render(request, 'runcard/barcode2.html', locals())

def search_for_runcard(request):
    try:
        period_times = ['6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17',
                        '18', '19', '20', '21', '22', '23', '0', '1', '2', '3', '4', '5']

        today_date = datetime.today() - timedelta(hours=5) + timedelta(minutes=39)# + timedelta(hours=14)
        # print('search today: ', today_date)
        last_7_days = [(today_date - timedelta(days=0) - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

        port = request.META.get('SERVER_PORT')
        if port == '10000':
            plant = 'NBR'
        if port == '10001':
            plant = 'PVC'
        sql01 = f"""SELECT id as mach_id, name as machine_name
                            FROM [PMGMES].[dbo].[PMG_DML_DataModelList]
                            WHERE DataModelTypeId = 'DMT000003'
                            and Abbreviation like '%{plant}%'
                            order by machine_name"""
        machine_lines_dicts = db_mes.select_sql_dict(sql01)
        nbr_lines = ['A1', 'B1', 'A2', 'B2']
        pvc_lines = ['A1', 'B1']
        if plant == 'PVC':
            machine_lines_name = [machine_lines_dict['machine_name'] for machine_lines_dict in machine_lines_dicts][:12]
        else:
            machine_lines_name = [machine_lines_dict['machine_name'] for machine_lines_dict in machine_lines_dicts]
        machine_lines_short = [str(machine_lines_dict['machine_name']).split('_')[-1] for machine_lines_dict in
                               machine_lines_dicts]
        machine_lines = zip(machine_lines_name, machine_lines_short)
        if request.method == "POST":
            form_type = request.POST.get('form_type')
            if form_type == 'form1':
                search_plant = request.POST.get("search_plant", "")
                search_mach = request.POST.get("search_mach", "")
                search_line = request.POST.get("search_line", "")
                search_date = request.POST.get("search_date", "")
                search_time = request.POST.get("search_time", "")
                sql03 = f"""SELECT rc.WorkOrderId, rc.Id, 
                            MAX(CASE WHEN ir.OptionName = 'Roll' THEN ir.InspectionValue END) AS Roll,
                            MAX(CASE WHEN ir.OptionName = 'Roll' THEN ir.InspectionStatus END) AS Roll_status,
                            MAX(CASE WHEN ir.OptionName = 'Cuff' THEN ir.InspectionValue END) AS Cuff,
                            MAX(CASE WHEN ir.OptionName = 'Cuff' THEN ir.InspectionStatus END) AS Cuff_status,
                            MAX(CASE WHEN ir.OptionName = 'Palm' THEN ir.InspectionValue END) AS Palm,
                            MAX(CASE WHEN ir.OptionName = 'Palm' THEN ir.InspectionStatus END) AS Palm_status,
                            MAX(CASE WHEN ir.OptionName = 'Finger' THEN ir.InspectionValue END) AS Finger,
                            MAX(CASE WHEN ir.OptionName = 'Finger' THEN ir.InspectionStatus END) AS Finger_status,
                            MAX(CASE WHEN ir.OptionName = 'FingerTip' THEN ir.InspectionValue END) AS FingerTip,
                            MAX(CASE WHEN ir.OptionName = 'FingerTip' THEN ir.InspectionStatus END) AS FingerTip_status,
                            MAX(CASE WHEN ir.OptionName = 'Weight' THEN ir.InspectionValue END) AS Weight,
                            max(case when ir.OptionName = 'Weight' then ir.InspectionStatus end) as Weight_status 
                            FROM [PMGMES].[dbo].[PMG_MES_RunCard] rc
                            left join [PMGMES].[dbo].[PMG_MES_IPQCInspectingRecord] ir 
                            on ir.RunCardId = rc.id
                            where WorkCenterTypeName = '{search_plant}' 
                            and MachineName = '{search_mach}' 
                            and LineName = '{search_line}' 
                            and ((Period > 5 and InspectionDate = '{search_date}')
                            or (Period <= 5 and InspectionDate = DATEADD(DAY, 1 , '{search_date}')))
                            and Period = '{search_time}'
                            group by rc.WorkOrderId, rc.Id
                            """
                id_dict = db_mes.select_sql_dict(sql03)
                id_dict_len = len(id_dict)
                if len(id_dict) > 0:
                    if id_dict_len == 1:
                        search_rc = id_dict[0]['Id']
                        s_barcode_svg = barcode_class(search_rc, writer=SVGWriter())
                        s_buffer = BytesIO()
                        s_barcode_svg.write(s_buffer)
                        search_barcode = base64.b64encode(s_buffer.getvalue()).decode('utf-8')
                        try:
                            search_roll = id_dict[0]['Roll']
                            search_rc_values = [
                                ['Cuộn biên', id_dict[0]['Roll'], id_dict[0]['Roll_status'], 'Cổ tay', id_dict[0]['Cuff'], id_dict[0]['Cuff_status'], 'Bàn tay', id_dict[0]['Palm'], id_dict[0]['Palm_status']],
                                ['Ngón tay', id_dict[0]['Finger'], id_dict[0]['Finger_status'], 'Đầu ngón', id_dict[0]['FingerTip'], id_dict[0]['FingerTip_status'], 'Trọng lượng', round(float(id_dict[0]['Weight']), 1), id_dict[0]['Weight_status']]]
                        except:
                            pass
                    else:
                        search_wo_list = [id['WorkOrderId'] for id in id_dict]
                        search_rc_list = [id['Id'] for id in id_dict]
                        search_barcode_list = []
                        search_rc_values = []
                        search_roll = []
                        for i in range(len(id_dict)):
                            search_rc = id_dict[i]['Id']
                            s_barcode_svg = barcode_class(search_rc, writer=SVGWriter())
                            s_buffer = BytesIO()
                            s_barcode_svg.write(s_buffer)
                            search_barcode = base64.b64encode(s_buffer.getvalue()).decode('utf-8')
                            search_barcode_list.append(search_barcode)
                            search_roll.append(id_dict[i]['Roll'] if id_dict[i]['Roll'] is not None else '')
                            try:
                                search_rc_values.append([
                                    ['Cuộn biên', id_dict[i]['Roll'], id_dict[i]['Roll_status'], 'Cổ tay',
                                     id_dict[i]['Cuff'], id_dict[i]['Cuff_status'], 'Bàn tay', id_dict[i]['Palm'],
                                     id_dict[i]['Palm_status']],
                                    ['Ngón tay', id_dict[i]['Finger'], id_dict[i]['Finger_status'], 'Đầu ngón',
                                     id_dict[i]['FingerTip'], id_dict[i]['FingerTip_status'], 'Trọng lượng',
                                     round(float(id_dict[i]['Weight']), 1) if id_dict[i]['Weight'] is not None else '', id_dict[i]['Weight_status']]])
                            except:
                                pass
                        search_rcs = zip(search_rc_list, search_barcode_list, search_rc_values, search_roll)
    except Exception as e:
        print(e)
        pass
    return render(request, 'runcard/search.html', locals())

def extract_kichco(input_string):
    try:
        db = vnedc_database()
        sql = f"""
            select distinct size 
            from 
            (SELECT TOP 1 prod_size_a1 AS size
            FROM [VNEDC].[dbo].[collection_daily_prod_info]
            WHERE prod_name_a1 = '{input_string}'
            UNION ALL
            SELECT TOP 1 prod_size_b1 AS size
            FROM [VNEDC].[dbo].[collection_daily_prod_info]
            WHERE prod_size_b1 = '{input_string}'
            UNION ALL
            SELECT TOP 1 prod_size_b2 AS size
            FROM [VNEDC].[dbo].[collection_daily_prod_info]
            WHERE prod_size_b2 = '{input_string}'
            UNION ALL
            SELECT TOP 1 prod_size_a2 AS size
            FROM [VNEDC].[dbo].[collection_daily_prod_info]
            WHERE prod_size_a2 = '{input_string}')
            as kichco
        """
        size = db.select_sql_dict(sql)
        if len(size) > 0:
            return size[0]['size']
            pass
        else:
            first_dash_index = input_string.find('-')
            if first_dash_index == -1:
                dash_substring = input_string
            else:
                second_dash_index = input_string.find('-', first_dash_index + 1)
                if second_dash_index == -1:
                    dash_substring = input_string[first_dash_index + 1:]
                else:
                    dash_substring = input_string[first_dash_index + 1:second_dash_index]
                substring = dash_substring.split(" ")[0]
            if substring.endswith('XXL') or substring.endswith('XXS'):
                result = substring[-3:]
            elif substring.endswith('XL') or substring.endswith('XS'):
                result = substring[-2:]
            else:
                result = substring[-1]

            if result not in ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL']:
                if dash_substring.find('XXS') > -1:
                    result = 'XXS'
                elif dash_substring.find('XXL') > -1:
                    result = 'XXL'
                elif dash_substring.find('XS') > -1:
                    result = 'XS'
                elif dash_substring.find('XL') > -1:
                    result = 'XL'
                elif dash_substring.find('S') > -1:
                    result = 'S'
                elif dash_substring.find('M') > -1:
                    result = 'M'
                elif dash_substring.find('L') > -1:
                    result = 'L'
                return result
            else:
                return result
    except Exception as e:
        print(e)
        return ' '