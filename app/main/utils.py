"""
    main.utils.py
    处理用户请求过程中的简单功能函数
"""


""" 将查询到的数据按照前端需要的格式进行处理 """
def serverSideOutput(data):
    rows = []
    for index, record in enumerate(data):
        row = {}
        # 病人ID
        row["id"] = record.patient_id
        # 病人姓名
        row["name"] = record.patient_name
        # 检测日期
        row["check_date"] = record.date.strftime('%Y-%m-%d %H:%M:%S')
        # 上传日期
        row["upload_date"] = record.upload_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 左/右眼
        row["eye_type"] = "<span>" 
        if record.lpath: 
            row["eye_type"] += """<a class="btn" onclick="getZoomSrc(this, '""" + record.lpath + """')">OS</a>"""
        else:
            row["eye_type"] += """<a class="btn" disabled>OS</a>"""
        row["eye_type"] += """</span><br /><span>"""    
        
        if record.rpath: 
            row["eye_type"] += """<a class="btn" onclick="getZoomSrc(this, '""" + record.rpath + """')">OD</a>"""
        else:
            row["eye_type"] += """<a class="btn" disabled>OD</a>"""
        row["eye_type"] += """</span>"""  
        
        # 系统结果
        row["system_result"] = "<span>"
        if record.left_model_result:
            row["system_result"] += """<label class="model_result">""" + record.left_model_result + """</label>"""
        else:
            row["system_result"] += """<label class="model_result">无信息</label>"""
        row["system_result"] += """</span><br /><span>"""
        
        if record.right_model_result:
            row["system_result"] += """<label class="model_result">""" + record.right_model_result + """</label>"""
        else:
            row["system_result"] += """<label class="model_result">无信息</label>"""
        row["system_result"] += """</span><br /><span><a class="btn btn-info btn-sm"
                onclick="return getReport('/get_reportimg?imgID=""" + record.right_report +"""', '""" + str(record.id) +  """')">
                <i class="icon-picture icon-large"></i> 查看诊断报告</a>
        </span>"""
        
        # 备注
        if record.remarks:
            row["remark"] = """<textarea class="dp_text form-control" name="remarks" style="width:100px; resize:none">""" + record.remarks + """</textarea>"""
            
            
            """<input type="text" class="dp_text form-control" name="remarks" style="width:100px"
                placeholder=" """ + record.remarks + """ ">"""
            
        else:
            row["remark"] = """<textarea class="dp_text form-control" name="remarks" style="width:100px; resize:none"></textarea>"""
            
            """<input type="text" class="dp_text form-control" name="remarks" style="width:100px"
                placeholder="">"""
        
        # 修改诊断结果
        row["change"] = """<a tabindex="0" class="btn btn-sm btn-info dp_update_single dp_data_toggle"
                               role="button" data-toggle="popover" onclick="update_result(this)" data-trigger="focus" data-content="修改成功">修改备注</a>"""
        if record.diagnosed is None or int(record.diagnosed) == 0:
            row["change"] += """
                            <a tabindex="0" class="btn btn-sm btn-info dp_update_single dp_data_toggle"
                               role="button" onclick="editReport({})">提交诊断</a>""".format(str(record.id))
        else:
            row["change"] += """
                            <a tabindex="0" class="btn btn-sm btn-warning dp_update_single dp_data_toggle"
                               role="button" onclick="get_dgReport('{}', {})">查看诊断</a>""".format(record.d_report, str(record.id))
        
        rows.append(row)
    return rows

""" 从前端请求值中提取查询关键词 """
def getSearchKeyWord(content):
    res = {}
    res["patient_id"] = content.get("patient_id").strip()
    res["patient_name"] = content.get("patient_name").strip()
    res["date_start"] = content.get("date_start").strip()
    res["date_end"] = content.get("date_end").strip()
    res["upload_time_start"] = content.get("upload_time_start").strip()
    res["upload_time_end"] = content.get("upload_time_end").strip()

    res["gestation_start"] = content.get("gestation_start").strip()
    res["gestation_end"] = content.get("gestation_end").strip()
    res["weight_min"] = content.get("weight_min").strip()
    res["weight_max"] = content.get("weight_max").strip()
    res["search_way"] = content.get("search_way").strip()
    res["check"] = content.get("check").strip()
    return res