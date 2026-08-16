"""Shared fixtures for gpu-cost-optimizer tests."""

import pytest


@pytest.fixture
def simple_workflow():
    return {
        "name": "test_workflow",
        "pipeline": "stable-diffusion",
        "model": "sd-xl-base",
        "scheduler": {
            "type": "euler_a",
            "steps": 50,
        },
        "resolution": [1024, 1024],
        "batch_size": 1,
        "guidance_scale": 7.5,
        "safety_checker": True,
        "vae_tiling": False,
    }


@pytest.fixture
def large_workflow():
    return {
        "name": "large_workflow",
        "pipeline": "stable-diffusion",
        "model": "sd-xl-base",
        "scheduler": {
            "type": "dpm++_2m",
            "steps": 50,
        },
        "resolution": [2048, 2048],
        "batch_size": 2,
        "guidance_scale": 8.0,
        "safety_checker": True,
        "vae_tiling": True,
    }


@pytest.fixture
def video_workflow():
    return {
        "name": "video_workflow",
        "pipeline": "stable-video-diffusion",
        "model": "svd-xt",
        "scheduler": {
            "type": "euler",
            "steps": 30,
        },
        "resolution": [1280, 720],
        "batch_size": 1,
        "guidance_scale": 3.0,
        "safety_checker": False,
        "vae_tiling": True,
        "frames": 25,
        "fps": 24,
    }
