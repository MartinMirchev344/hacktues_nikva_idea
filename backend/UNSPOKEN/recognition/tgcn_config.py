import configparser


class TGCNConfig:
    def __init__(self, config_path):
        parser = configparser.ConfigParser()
        parser.read(config_path)

        train_config = parser["TRAIN"]
        optimizer_config = parser["OPTIMIZER"]
        gcn_config = parser["GCN"]

        self.batch_size = int(train_config["BATCH_SIZE"])
        self.max_epochs = int(train_config["MAX_EPOCHS"])
        self.log_interval = int(train_config["LOG_INTERVAL"])
        self.num_samples = int(train_config["NUM_SAMPLES"])
        self.drop_p = float(train_config["DROP_P"])

        self.init_lr = float(optimizer_config["INIT_LR"])
        self.adam_eps = float(optimizer_config["ADAM_EPS"])
        self.adam_weight_decay = float(optimizer_config["ADAM_WEIGHT_DECAY"])

        self.hidden_size = int(gcn_config["HIDDEN_SIZE"])
        self.num_stages = int(gcn_config["NUM_STAGES"])

