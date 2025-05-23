import torch
import argparse
import sys

from network import RnnFactory

class Setting:
    
    ''' Defines all settings in a single place using a command line interface.
    '''
    
    def parse(self):
        # sys.argv: 命令行参数列表，sys.argv[0]是脚本名，后续元素是执行脚本时传入的其他参数
        # 只要命令行参数中有一个参数包含'4sq'，即数据集是Foursquare时，guess_foursquare就为True
        self.guess_foursquare = any(['4sq' in argv for argv in sys.argv]) # Foursquare has different default args with Gowalla.
                
        parser = argparse.ArgumentParser()        
        if self.guess_foursquare:
            self.parse_foursquare(parser)
        else:
            self.parse_gowalla(parser)        
        self.parse_arguments(parser)
        # 返回一个包含所有参数的命名空间对象（argparse.Namespace 类型），可以通过属性方式访问参数                
        args = parser.parse_args()
        
        ###### settings ######
        # training
        self.gpu = args.gpu
        self.hidden_dim = args.hidden_dim
        self.weight_decay = args.weight_decay
        self.learning_rate = args.lr
        self.epochs = args.epochs
        # 拥有create the desired RNN unit能力的对象
        self.rnn_factory = RnnFactory(args.rnn)
        self.is_lstm = self.rnn_factory.is_lstm()
        self.lambda_t = args.lambda_t
        self.lambda_s = args.lambda_s
        
        # data management
        self.dataset_file = './data/{}'.format(args.dataset)
        self.max_users = 0 # 当 max_users<=0 时，就会 use all available users
        self.sequence_length = 20
        self.batch_size = args.batch_size
        self.min_checkins = 101
        
        # evaluation        
        self.validate_epoch = args.validate_epoch
        self.report_user = args.report_user        
     
        ### CUDA Setup ###
        self.device = torch.device('cpu') if args.gpu == -1 else torch.device('cuda', args.gpu)        
    
    def parse_arguments(self, parser):        
        # training
        parser.add_argument('--gpu', default=-1, type=int, help='the gpu to use')        
        parser.add_argument('--hidden-dim', default=10, type=int, help='hidden dimensions to use')
        parser.add_argument('--weight_decay', default=0.0, type=float, help='weight decay regularization')
        parser.add_argument('--lr', default = 0.01, type=float, help='learning rate')
        parser.add_argument('--epochs', default=100, type=int, help='amount of epochs')
        parser.add_argument('--rnn', default='rnn', type=str, help='the RNN implementation to use: [rnn|gru|lstm]')        
        
        # data management
        parser.add_argument('--dataset', default='checkins-gowalla.txt', type=str, help='the dataset under ./data/<dataset.txt> to load')        
        
        # evaluation        
        parser.add_argument('--validate-epoch', default=5, type=int, help='run each validation after this amount of epochs')
        parser.add_argument('--report-user', default=-1, type=int, help='report every x user on evaluation (-1: ignore)')        
    
    def parse_gowalla(self, parser):
        # defaults for gowalla dataset
        parser.add_argument('--batch-size', default=200, type=int, help='amount of users to process in one pass (batching)')
        parser.add_argument('--lambda_t', default=0.1, type=float, help='decay factor for temporal data')
        parser.add_argument('--lambda_s', default=1000, type=float, help='decay factor for spatial data')
    
    def parse_foursquare(self, parser):
        # defaults for foursquare dataset
        parser.add_argument('--batch-size', default=1024, type=int, help='amount of users to process in one pass (batching)')
        parser.add_argument('--lambda_t', default=0.1, type=float, help='decay factor for temporal data')
        parser.add_argument('--lambda_s', default=100, type=float, help='decay factor for spatial data')
    
    # print(类实例) 时自动调用
    def __str__(self):        
        return ('parse with foursquare default settings' if self.guess_foursquare else 'parse with gowalla default settings') + '\n'\
            + 'use device: {}'.format(self.device)


        