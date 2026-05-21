from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/stats")
def system_stats():
    try:
        import psutil
    except ImportError:
        return {
            "memory_percent": 0,
            "memory_total_gb": 0,
            "cpu_percent": 0,
            "network": "Unknown (install psutil)",
            "detail": False,
        }

    vm = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.15)
    return {
        "memory_percent": round(vm.percent, 1),
        "memory_total_gb": round(vm.total / (1024**3), 1),
        "cpu_percent": round(cpu, 1),
        "network": "Connected (LAN)",
        "detail": True,
    }
