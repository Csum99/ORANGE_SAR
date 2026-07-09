# Backprojection



## 1. File Organization

- `mit_data/`
  - `collect_4.prd`: The raw radar data
  - `mocap_data_004.csv`: The raw motion capture data
- `mocap/`
  - `calibration_auto.py`: Script for interactive time alignment
  - `data_processor.py`: Preprocess the raw radar data and motion capture data



## 2. Install the required packages

Activate the python virtual environment, then

```
cd mocap/

pip install -r pip_requirements.txt
```





## 3. Steps

1. Unpack the raw radar data by

   ```
   cd pulson440/
   
   python unpack.py ../mit_data/collect_4.prd -v --keep_clutter 
   ```

   Then you will see `collect_4.gif`, `collect_4.png`, and `collect_4.pkl` under `pulson440/`. Move `collect_4.pkl` to the folder `mit_data/`.

   

2. Do data preprocessing by

   ```
   cd mocap/
   
   python data_processor.py ../mit_data/collect_4.pkl ../mit_data/mocap_data_004.csv --platform-name Radar --corner-right-name Corner_R --corner-left-name Corner_L --save-plots --save-data
   ```

   where `--platform-name`, `--corner-right-name` and `--corner-left-name` are the name of the radar and two reflectors in `mocap_data_004.csv`. When you see `Do you want to swap the coordinate order to (z, x, y)?`, type `y` to swap the axes. Then you will see some pictures showing the position of radar and reflectors.

   

   When you see `Do you want to proceed with radar data processing? (y/n):`, type `y`. Then you will see an RTI image, as well as an interactive plot as follows

   

   ![image-20250731152738443](/Users/xl/Library/Application Support/typora-user-images/image-20250731152738443.png)

   You need to align the red and orange curve to the pattern in the image, by sliding the bar of `start Bin`. After finishing alignment, press Confirm. You will see `mocap_data_004.pkl` under `mocap/`, move it to `mit_data/`.

   ![image-20250731153045128](/Users/xl/Library/Application Support/typora-user-images/image-20250731153045128.png)

   

3. Time alignment for motion capture data and radar data. Run

```
python calibration_auto.py ../mit_data/collect_4.pkl ../mit_data/mocap_data_004.pkl --sigma 0.3
```

When you see `Which reflector to use for alignment? (1 or 2): `, press 1 (2) if choosing the left (right) reflector. Then you will see

![image-20250731155327813](/Users/xl/Library/Application Support/typora-user-images/image-20250731155327813.png)

Close this image, then the program will spend few minutes on plotting the X-axis movement. Do not shut down the program! Finally you will see an interactive GUI as follows

![image-20250731155538214](/Users/xl/Library/Application Support/typora-user-images/image-20250731155538214.png)

Slide the bar of velocity threshold to select a reasonable range, then press Confirm.

![image-20250731162138822](/Users/xl/Library/Application Support/typora-user-images/image-20250731162138822.png)



You will see `run_0.pkl` under `backprojection/`, which will be used for backprojection.



4. Finally, run backprojection by

```
cd ../backprojection/

python backprojection.py run_0.pkl -1.7 1.5 0.01 -1.2 2.7 0.01 -p
```

Tune the arguments if needed. If your backprojection works, then you will see an image similar to this

![image-20250731161730433](/Users/xl/Library/Application Support/typora-user-images/image-20250731161730433.png)



