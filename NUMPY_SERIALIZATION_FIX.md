# Numpy Serialization Fix Summary

## Error Fixed
```
pydantic_core._pydantic_core.PydanticSerializationError: Unable to serialize unknown type: <class 'numpy.ndarray'>
```

## Root Cause
The simulation agent was returning numpy scalar types (numpy.float64, numpy.int64) which Pydantic cannot serialize to JSON.

## Files Modified

### 1. `app/sub_agents/simulation_agent/engine.py`
**Problem:** `compute_metrics()` returned numpy types  
**Solution:** Explicitly convert all numpy types to Python native types

```python
def compute_metrics(simulated_changes):
    """
    Compute VaR and yield range metrics from simulated changes.
    Ensures all return values are JSON-serializable Python types.
    """
    return {
        "VaR_95_YieldBps": float(round(np.percentile(simulated_changes, 5) * 10000, 2)),
        "YieldRange_Bps": [
            float(round(simulated_changes.min() * 10000, 2)),
            float(round(simulated_changes.max() * 10000, 2))
        ],
        "SimCount": int(SIM_COUNT)
    }
```

### 2. `app/sub_agents/simulation_agent/tools.py`
**Problem:** No validation and potential for numpy leakage  
**Solution:** Added validation and ensured clean interface

```python
def simulate_bond_risk(ForecastedYields: dict, RegimeHint: str = "normal", ConfidenceScore: float | None = None):
    # Validate regime
    if RegimeHint not in STRESS_REGIMES:
        return {"error": f"Invalid RegimeHint..."}
    
    results = {}
    for tenor in ForecastedYields.keys():
        if tenor not in TENOR_MAP:
            results[tenor] = {"error": f"Invalid tenor..."}
            continue
        
        try:
            simulated_changes = simulate_yield_changes(tenor, RegimeHint)
            results[tenor] = compute_metrics(simulated_changes)  # Returns Python types
        except Exception as e:
            results[tenor] = {"error": str(e)}
    
    return results  # All JSON-serializable
```

## Return Format

**Before (Broken):**
```python
{
    "5Y": {
        "VaR_95_YieldBps": numpy.float64(-12.34),    # ❌ Not serializable
        "YieldRange_Bps": [numpy.float64(-45.67), numpy.float64(89.01)],  # ❌
        "SimCount": numpy.int64(10000)               # ❌
    }
}
```

**After (Fixed):**
```python
{
    "5Y": {
        "VaR_95_YieldBps": -12.34,        # ✅ Python float
        "YieldRange_Bps": [-45.67, 89.01], # ✅ Python floats in list
        "SimCount": 10000                  # ✅ Python int
    }
}
```

## Type Conversions Applied
- `numpy.float64` → `float()` ✅
- `numpy.int64` → `int()` ✅  
- `numpy.ndarray` → Not returned (only extracted values) ✅

## Test Compatibility
The return format maintains backward compatibility with existing unit tests:
- ✅ `test_simulate_bond_risk_single_tenor()` expects `result["5Y"]`
- ✅ All metrics are Python native types as expected
- ✅ Error handling with clear messages

## Verification
All values returned are now JSON-serializable Python types, ensuring Pydantic can serialize the response for the ADK framework.

**Date Fixed:** December 15, 2025  
**Commits:**
- Fixed numpy type conversions in engine.py
- Simplified tools.py return format for compatibility

