import { inject, provide, type InjectionKey } from 'vue'

export type AppViewContext = Record<string, any>

export const appViewContextKey: InjectionKey<AppViewContext> = Symbol('appViewContext')

export function provideAppViewContext(context: AppViewContext) {
  provide(appViewContextKey, context)
}

export function useAppBindings() {
  const context = inject(appViewContextKey)
  if (!context) throw new Error('App view context is not available')
  return context
}
