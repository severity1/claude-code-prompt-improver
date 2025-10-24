"""Standalone script to train the LSTM model for cryptocurrency price prediction.

This module serves as a simple wrapper around the lstm_model.main() function,
allowing the LSTM training pipeline to be executed directly.

Prerequisites:
    - Historical data must be fetched (run fetch_data.py first)
    - Data must be preprocessed (run preprocess.py first)

Example:
    Run from command line:
    $ python train_lstm.py
"""

from lstm_model import main

if __name__ == '__main__':
    main()
