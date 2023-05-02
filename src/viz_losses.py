import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def lineplot(title, dir, save_path):

    df = pd.DataFrame()
    for file in os.listdir(dir):
        if file.endswith(".csv"):
            df_ = pd.read_csv(f"{dir}/{file}")
            df_["Dataset"] = file.split(".")[0]
            df_.drop(columns=["Wall time"], inplace=True)
            df = pd.concat([df, df_])

    fig, ax = plt.subplots()
    sns.lineplot(data=df, x="Step", y="Value",
             hue="Dataset",
             hue_order=['Sat2pc (baseline)',
                        "2 and 4 surfaces (unbalanced)",
                        "2 and 4 surfaces (balanced)",
                        "2 surfaces",
                        "4 surfaces"])

    ax.set_ylim(0, 0.6)
    #ax.set_xlim(0, 1000)

    ax.set_xlabel("Step")
    ax.set_ylabel("Total loss value")
    ax.set_title(title)

    plt.savefig(save_path)
    plt.show()


lineplot(title = "Loss development on train set",
         dir = "figures/losses/sat2pc_train",
         save_path="figures/loss_train.png"
         )

lineplot(title = "Loss development on validation set",
         dir = "figures/losses/sat2pc_val",
         save_path="figures/loss_val.png"
         )

