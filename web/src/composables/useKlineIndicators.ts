import { ref } from 'vue'

export function useKlineIndicators() {
  const showVwap = ref(true)
  const showMa = ref(false)
  const showEma = ref(false)
  const showBollinger = ref(false)
  const maPeriod = ref(20)
  const emaPeriod = ref(20)
  const bollingerPeriod = ref(20)
  const bollingerMultiplier = ref(2)
  const activeParamDialog = ref<'ma' | 'ema' | 'boll' | ''>('')

  function openSimpleParamDialog(type: 'ma' | 'ema' | 'boll') {
    activeParamDialog.value = type
  }

  function closeSimpleParamDialog() {
    activeParamDialog.value = ''
  }

  function simpleParamTitle() {
    const titles: Record<string, string> = {
      ma: 'MA 参数',
      ema: 'EMA 参数',
      boll: 'BOLL 参数'
    }
    return titles[activeParamDialog.value] || '指标参数'
  }

  return {
    showVwap,
    showMa,
    showEma,
    showBollinger,
    maPeriod,
    emaPeriod,
    bollingerPeriod,
    bollingerMultiplier,
    activeParamDialog,
    openSimpleParamDialog,
    closeSimpleParamDialog,
    simpleParamTitle
  }
}
