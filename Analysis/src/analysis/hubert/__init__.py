"""HuBERT phonological-subspace extension of the voice-cycle study.

A third, independent measurement family alongside the whole-recording eGeMAPS
study and the phoneme-grain study. Where those measure named acoustic
properties, this measures the *representational separability* of phonological
categories in frozen self-supervised speech embeddings - the d-prime
"phonological subspace" of Muller et al. 2026 (arXiv:2604.21706) - and asks
whether that separability moves with the menstrual cycle within one speaker.

The d-prime tables (one per SSL backbone) are produced upstream in
SpeechFeatureExtraction over the shared MFA boundaries; this package does only
the cycle-phase join, statistics, triangulation, and figures.
"""
