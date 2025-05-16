import os.path
import sys

from datetime import datetime

from dataset import PoiDataset, Usage

class PoiDataloader():
    ''' Creates datasets from our prepared Gowalla/Foursquare data files.
    The file consist of one check-in per line in the following format (tab separated):    
    
    <user-id> <timestamp> <latitude> <longitude> <location-id> 
    
    Check-ins for the same user have to be on continous lines.
    Ids for users and locations are recreated and continous from 0.
    '''
    
    def __init__(self, max_users=0, min_checkins=0):
        ''' max_users limits the amount of users to load.
        min_checkins discards users with less than this amount of checkins.               
        '''
        
        self.max_users = max_users
        self.min_checkins = min_checkins
        
        self.user2id = {}
        self.poi2id = {}
        
        self.users = []
        self.times = []
        self.coords = []
        self.locs = []
    
    def create_dataset(self, sequence_length, batch_size, split, usage=Usage.MAX_SEQ_LENGTH, custom_seq_count=1):
        # copy()是浅拷贝，则对于一个二维列表，修改外层列表，不会影响原列表，但是修改原内层列表，原列表会同步更改
        return PoiDataset(self.users.copy(),
                          self.times.copy(),
                          self.coords.copy(),
                          self.locs.copy(),
                          sequence_length,
                          batch_size,
                          split,
                          usage,
                          len(self.poi2id),
                          custom_seq_count)
        
    
    def user_count(self):
        return len(self.users)
    
    def locations(self):
        return len(self.poi2id)
    
    def read(self, file):
        if not os.path.isfile(file):
            print('[Error]: Dataset not available: {}. Please follow instructions under ./data/README.md'.format(file))
            sys.exit(1)

        # collect all users with min checkins:
        self.read_users(file)
        # collect checkins for all collected users:
        self.read_pois(file)
    
    '''
    def read_users(self, file):        
        with open(file, 'r') as f:            
            lines = f.readlines()
            prev_user = int(lines[0].split('\t')[0])
            visit_cnt = 0
            for i, line in enumerate(lines):
                tokens = line.strip().split('\t')
                user = int(tokens[0])
                if user == prev_user:
                    visit_cnt += 1
                else:
                    if visit_cnt >= self.min_checkins:
                        self.user2id[prev_user] = len(self.user2id)
                    #else:
                    #    print('discard user {}: to few checkins ({})'.format(prev_user, visit_cnt))
                    prev_user = user
                    visit_cnt = 1
                    if self.max_users > 0 and len(self.user2id) >= self.max_users:
                        break # restrict to max users
    '''
    
    def read_users(self, file):
        with open(file, 'r') as f:
            prev_user = None
            visit_cnt = 0
            break_occurred = False

            for line in f:
                tokens = line.strip().split('\t')
                user = int(tokens[0])

                if prev_user is None:
                    prev_user = user
                    visit_cnt = 1
                    continue

                if user == prev_user:
                    visit_cnt += 1
                else:
                    if visit_cnt >= self.min_checkins:
                        self.user2id[prev_user] = len(self.user2id)
                    # else:
                    #     print(f'discard user {prev_user}: too few checkins ({visit_cnt})')
                    prev_user = user
                    visit_cnt = 1
                    if self.max_users > 0 and len(self.user2id) >= self.max_users:
                        break_occurred = True
                        break
            # 处理最后一个用户
            if not break_occurred and prev_user is not None and visit_cnt >= self.min_checkins:
                self.user2id[prev_user] = len(self.user2id)                    

    def read_pois(self, file):
        '''
        self.users   → [user0_id, user1_id, ..., userN_id]           # 用户 ID 列表
        self.times   → [[t1, t2, ...], [t1, t2, ...], ...]           # 每个用户的签到时间序列（按时间倒序）
        self.coords  → [[(lat, lon), ...], [(lat, lon), ...], ...]   # 每个用户的签到坐标序列（按时间倒序）
        self.locs    → [[loc1, loc2, ...], [loc1, loc2, ...], ...]   # 每个用户的新位置编号序列（按时间倒序）
        self.poi2id  → {原始location_id: 新ID}                       # 全部位置的映射表
        '''
        with open(file, 'r') as f:
            # store location ids
            user_time = []
            user_coord = []
            user_loc = []
            
            line = f.readline()
            prev_user = int(line.strip().split('\t')[0])
            prev_user_id = self.user2id.get(prev_user)
            
            f.seek(0)
            for line in f:
                tokens = line.strip().split('\t')
                user = int(tokens[0])
                if self.user2id.get(user) is None:
                    continue # user is not of interest
                user_id = self.user2id.get(user)
                # datetime.strptime(tokens[1], "%Y-%m-%dT%H:%M:%SZ"): datetime.datetime(2013, 12, 20, 15, 24, 43)
                # T 是 ISO 8601 标准中用于连接日期和时间的分隔符
                # Z 表示时间是在 UTC 时间（零时区）     
                time = (datetime.strptime(tokens[1], "%Y-%m-%dT%H:%M:%SZ") - datetime(1970, 1, 1)).total_seconds() # unix seconds
                lat = float(tokens[2])
                long = float(tokens[3])
                coord = (lat, long)            
                location = int(tokens[4]) # location nr
                if self.poi2id.get(location) is None: # get-or-set locations
                    self.poi2id[location] = len(self.poi2id)
                location_id = self.poi2id.get(location)
        
                if user_id == prev_user_id:
                    # insert in front!
                    user_time.insert(0, time)
                    user_coord.insert(0, coord)
                    user_loc.insert(0, location_id)
                else:
                    self.users.append(prev_user_id)
                    self.times.append(user_time)
                    self.coords.append(user_coord)
                    self.locs.append(user_loc)
                    
                    # restart:
                    prev_user_id = user_id 
                    user_time = [time]
                    user_coord = [coord]
                    user_loc = [location_id] 
                    
            # process also the latest user in the for loop
            self.users.append(prev_user_id)
            self.times.append(user_time)
            self.coords.append(user_coord)
            self.locs.append(user_loc)
