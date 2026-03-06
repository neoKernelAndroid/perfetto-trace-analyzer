# -*- coding: utf-8 -*-
# @Time     : 2025/2/27 15:52
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : PerfettoSqlCommon.py
import re

from modules.common.Logger import TEST_LOGGER


class Slice(object):
    def __init__(self):
        self.id = None
        self.name = None
        self.ts = None
        self.te = None
        self.dur = None
        self.process_name = None
        self.thread_name = None
        self.category = None



def get_startup_info(tp, package_name=None, startup_type=None):
    """
    获取启动信息，开始时间、启动耗时等
    :param tp:
    :param package_name: 启动包名
    :param startup_type: 启动类型，hot|cold|warm
    :return:
    """
    if package_name and startup_type:
        sql = f"""
        SELECT IMPORT('android.startup.startups');
        SELECT * FROM android_startups where package = "{package_name}" and startup_type = "{startup_type}";
        """
    elif package_name:
        sql = f"""
        SELECT IMPORT('android.startup.startups');
        SELECT * FROM android_startups where package = "{package_name}"
        """
    elif startup_type:
        sql = f"""
        SELECT IMPORT('android.startup.startups');
        SELECT * FROM android_startups where startup_type = "{startup_type}";
        """
    else:
        sql = f"""
        SELECT IMPORT('android.startup.startups');
        SELECT * FROM android_startups;
        """
    startup_info_list = []
    query_rlt = tp.query(sql)
    for row in query_rlt:
        ts = row.ts
        ts_end = row.ts_end
        dur = row.dur
        package_name = row.package
        startup_type = row.startup_type
        startup_id = row.startup_id
        startup_info_list.append({
            "startup_id": startup_id,
            "ts": ts,
            "ts_end": ts_end,
            "dur": dur,
            "package_name": package_name,
            "startup_type": startup_type
        })

    return startup_info_list


def get_translation_info(tp, transition_id=None, package_name=None):
    """
    获取activity切换信息
    :param tp:
    :param transition_id:
    :return:
    """
    startup_info_list = []
    if transition_id:
        sql = f"""
        select * from slice where name like "launchingActivity#{transition_id}:%"
        """
        query_rlt = tp.query(sql)
        for row in query_rlt:
            name = row.name
            split_name = name.split(":")
            if len(split_name) == 3:
                transition_tag = split_name[0]
                transition_type = split_name[1]
                package = split_name[2]
            else:
                ts = row.ts
                dur = row.dur
                ts_end = ts + dur

        startup_info_list.append({
            "transition_id": transition_id,
            "ts": ts,
            "ts_end": ts_end,
            "dur": dur,
            "package_name": package,
            "transition_type": transition_type
        })
    else:
        sql = f"""
        select * from slice where name like "launchingActivity#%"
        """
        query_rlt = tp.query(sql)

        target_tag_dict = {}
        query_rlt_list = []
        for row in query_rlt:
            query_rlt_list.append(row)
            name = row.name
            # 首先根据name过滤掉无效信息
            if package_name:
                if package_name in name:
                    split_name = name.split(":")
                    if len(split_name) == 3:
                        transition_tag = split_name[0]
                        transition_type = split_name[1]
                        package = split_name[2]
                        target_tag_dict[transition_tag] = [transition_type, package]
            else:
                if ":failed" in name:
                    continue
                split_name = name.split(":")
                if len(split_name) == 3:
                    transition_tag = split_name[0]
                    transition_type = split_name[1]
                    package = split_name[2]
                    target_tag_dict[transition_tag] = [transition_type, package]

        if target_tag_dict:
            for row in query_rlt_list:
                name = row.name
                if name in target_tag_dict:
                    ts = row.ts
                    dur = row.dur
                    ts_end = ts + dur
                    transition_id = name.split("#")[1]
                    startup_info_list.append({
                        "transition_id": transition_id,
                        "ts": ts,
                        "ts_end": ts_end,
                        "dur": dur,
                        "package_name": package,
                        "transition_type": transition_type
                    })

    return startup_info_list


def get_choreographer_doFrame(tp, package_name):
    sql = f"""
    select slice.ts, slice.dur, slice.name from slice 
    JOIN thread_track ON (thread_track.id = slice.track_id) 
    JOIN thread ON (thread.utid = thread_track.utid) 
    where slice.name like '%Choreographer#doFrame%' and thread.name = '{package_name}'
    """
    pattern_doFrame_vsync = re.compile(r"Choreographer#doFrame (\d+)")

    doFrame_dict = {}
    query_rlt = tp.query(sql)
    for row in query_rlt:
        print(row)
        ts = row.ts
        dur = row.dur
        ts_end = ts + dur
        name = row.name
        matches = re.match(pattern_doFrame_vsync, name)
        if matches:
            vsync_id = matches.group(1)
            doFrame_dict[vsync_id] = ts
    return doFrame_dict


def get_render_thread_drowFrames(tp):
    sql = """
    select slice.ts, slice.dur, slice.name from slice
    JOIN thread_track ON (thread_track.id = slice.track_id) 
    JOIN thread ON (thread.utid = thread_track.utid) 
    JOIN process p ON thread.upid = p.upid 
    where slice.name like '%DrawFrames%' and thread.name = 'RenderThread'
    """
    pattern_draw_frames_vsync = re.compile(r"DrawFrames (\d+)")

    drawFrames_dict = {}
    query_rlt = tp.query(sql)
    for row in query_rlt:
        ts = row.ts
        dur = row.dur
        ts_end = ts + dur
        name = row.name
        matches = re.match(pattern_draw_frames_vsync, name)
        if matches:
            vsync_id = matches.group(1)
            drawFrames_dict[vsync_id] = ts_end
    return drawFrames_dict


def get_dequeueBuffer(tp):
    sql = """
    select * from slice 
    JOIN thread_track ON (thread_track.id = slice.track_id) 
    JOIN thread ON (thread.utid = thread_track.utid) 
    JOIN process p ON thread.upid = p.upid 
    where slice.name = 'dequeueBuffer' and thread.name = 'RenderThread'
    """
    dequeueBuffer_list = []
    query_rlt = tp.query(sql)
    for row in query_rlt:
        ts = row.ts
        dur = row.dur
        ts_end = ts + dur
        dequeueBuffer_list.append([ts, ts_end, dur])
    return dequeueBuffer_list


def get_vsync_sf(tp):
    sql = """
    select c.ts as ts from counter as c left join process_counter_track as t on c.track_id = t.id
    where t.name = 'VSYNC-sf'
    """
    vsync_sf_list = []
    query_rlt = tp.query(sql)
    for row in query_rlt:
        vsync_sf_list.append(row.ts)
    return vsync_sf_list


def get_backpressure(tp):
    sql = """
    select ts, dur from slice where name = 'backpressure'
    """
    backpressure_list = []
    query_rlt = tp.query(sql)
    for row in query_rlt:
        ts = row.ts
        dur = row.dur
        ts_end = ts + dur
        backpressure_list.append([ts, ts_end, dur])
    return backpressure_list


def get_slice_by_name_via_thread(tp, slice_name_tag, process_name, order_by_asc=True):
    slice_list = []
    sql = f"""
        SELECT slice.slice_id, slice.ts, slice.dur, slice.name, slice.track_id, p.name as process_name, thread.name as thread_name 
        FROM slice 
        JOIN thread_track ON (thread_track.id = slice.track_id) 
        JOIN thread ON (thread.utid = thread_track.utid)
        JOIN process p ON thread.upid = p.upid
        WHERE slice.name like '%{slice_name_tag}%' and process_name='{process_name}'
        order by slice.ts {'ASC' if order_by_asc else 'DESC'};
    """

    TEST_LOGGER.info(f"开始获取slice_name_tag:[{slice_name_tag}], process_name:[{process_name}] 的slice 信息")
    TEST_LOGGER.info(f"sql:{sql}")
    query_rlt = tp.query(sql)
    for row in query_rlt:
        slice_obj = Slice()
        slice_obj.id = row.slice_id
        slice_obj.name = row.name
        slice_obj.track_id = row.track_id
        slice_obj.ts = row.ts
        slice_obj.dur = row.dur
        slice_obj.te = row.ts + row.dur
        slice_obj.process_name = row.process_name
        slice_obj.thread_name = row.thread_name
        slice_list.append(slice_obj)

    return slice_list


def get_slice_by_name_via_process(tp, slice_name_tag, process_name, order_by_asc=True):
    slice_list = []
    sql = f"""
        SELECT slice.slice_id, slice.ts, slice.dur, slice.name, slice.track_id, p.name as process_name 
        FROM slice 
        JOIN process_track ON slice.track_id = process_track.id
        JOIN process p ON process_track.upid = p.upid
        WHERE slice.name like '%{slice_name_tag}%' and process_name='{process_name}'
        order by slice.ts {'ASC' if order_by_asc else 'DESC'};
    """

    TEST_LOGGER.info(f"开始获取slice_name_tag:[{slice_name_tag}], process_name:[{process_name}] 的slice 信息")
    TEST_LOGGER.info(f"sql:{sql}")
    query_rlt = tp.query(sql)
    for row in query_rlt:
        slice_obj = Slice()
        slice_obj.id = row.slice_id
        slice_obj.name = row.name
        slice_obj.track_id = row.track_id
        slice_obj.ts = row.ts
        slice_obj.dur = row.dur
        slice_obj.te = row.ts + row.dur
        slice_obj.process_name = row.process_name
        slice_list.append(slice_obj)

    return slice_list


def get_start_package_name(tp, slice_name_tag, ignore_package=None, order_by_asc=True):
    if slice_name_tag is None:
        start_package_dict = {}
    else:
        sql = f"""
        SELECT ts, dur, name from slice where name like '%{slice_name_tag}%' order by ts {'ASC' if order_by_asc else 'DESC'};
        """
        TEST_LOGGER.info(f"开始通过[{slice_name_tag}]获取启动应用的包名")
        TEST_LOGGER.info(f"sql:{sql}")

        start_package_dict = {}
        query_rlt = tp.query(sql)
        for row in query_rlt:
            ts = row.ts
            name = row.name
            if ignore_package and ignore_package in name:
                continue
            process_name = name.split(" ")[-1]
            start_package_dict[ts] = process_name

    if not start_package_dict:
        # 如果获取到的start_package_dict为空，则通过android_startups获取
        sql = f"""
        SELECT IMPORT('android.startup.startups');
        SELECT ts, dur, package FROM android_startups order by ts {'ASC' if order_by_asc else 'DESC'};
        """
        TEST_LOGGER.info(f"开始通过android.startup.startups获取启动应用的包名")
        TEST_LOGGER.info(f"sql:{sql}")

        start_package_dict = {}
        query_rlt = tp.query(sql)
        for row in query_rlt:
            ts = row.ts
            name = row.package
            process_name = name.split(" ")[-1]
            start_package_dict[ts] = process_name

    return start_package_dict


def get_process_thread_count(tp, process_name):
    """
    获取指定进程的线程数量和线程详细信息
    :param tp: TraceProcessor对象
    :param process_name: 进程名称，如 'system_server', 'com.android.systemui', 'com.android.launcher3'
    :return: 字典，包含线程数量和线程列表
    """
    sql = f"""
    SELECT 
        thread.name as thread_name,
        thread.tid as tid,
        thread.utid as utid,
        process.name as process_name,
        process.pid as pid
    FROM thread
    JOIN process USING(upid)
    WHERE process.name = '{process_name}'
    ORDER BY thread.tid;
    """
    
    thread_list = []
    query_rlt = tp.query(sql)
    for row in query_rlt:
        thread_info = {
            'thread_name': row.thread_name,
            'tid': row.tid,
            'utid': row.utid,
            'process_name': row.process_name,
            'pid': row.pid
        }
        thread_list.append(thread_info)
    
    return {
        'process_name': process_name,
        'thread_count': len(thread_list),
        'threads': thread_list
    }


def get_all_process_thread_count(tp, top_n=20):
    """
    获取所有进程的线程数统计，按线程数降序排列
    :param tp: TraceProcessor对象
    :param top_n: 返回前N个进程，默认20个
    :return: 进程线程数统计列表
    """
    sql = f"""
    SELECT 
        process.name as process_name,
        process.pid as pid,
        COUNT(DISTINCT thread.utid) as thread_count
    FROM thread
    JOIN process USING(upid)
    GROUP BY process.name, process.pid
    ORDER BY thread_count DESC
    LIMIT {top_n};
    """
    
    process_list = []
    query_rlt = tp.query(sql)
    for row in query_rlt:
        process_info = {
            'process_name': row.process_name,
            'pid': row.pid,
            'thread_count': row.thread_count
        }
        process_list.append(process_info)
    
    return process_list


def get_multiple_process_thread_count(tp, process_names):
    """
    批量获取多个进程的线程数
    :param tp: TraceProcessor对象
    :param process_names: 进程名称列表，如 ['system_server', 'com.android.systemui']
    :return: 进程线程数统计字典
    """
    if not process_names:
        return {}
    
    # 构建 IN 查询条件
    process_names_str = "', '".join(process_names)
    sql = f"""
    SELECT 
        process.name as process_name,
        process.pid as pid,
        COUNT(DISTINCT thread.utid) as thread_count
    FROM thread
    JOIN process USING(upid)
    WHERE process.name IN ('{process_names_str}')
    GROUP BY process.name, process.pid
    ORDER BY thread_count DESC;
    """
    
    result_dict = {}
    query_rlt = tp.query(sql)
    for row in query_rlt:
        result_dict[row.process_name] = {
            'pid': row.pid,
            'thread_count': row.thread_count
        }
    
    return result_dict