import { useEffect, useState } from 'react'
import { useLocation, type Location } from 'react-router-dom'
import { getProducts } from './api.ts'
import type { Product } from './types.ts'

export interface ModalState {
  backgroundLocation?: Location
}

/**
 * Link props that open a product in the modal over the current page.
 * If a modal is already open, keep its original background and replace the entry.
 */
export function useProductModalLink(): { state: ModalState; replace: boolean } {
  const location = useLocation()
  const existing = (location.state as ModalState | null)?.backgroundLocation
  return { state: { backgroundLocation: existing ?? location }, replace: Boolean(existing) }
}

export type LoadState<T> =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: T }

/** Loads the full catalogue once per mount. */
export function useProducts(): LoadState<Product[]> {
  const [state, setState] = useState<LoadState<Product[]>>({ status: 'loading' })

  useEffect(() => {
    let active = true
    getProducts()
      .then((data) => active && setState({ status: 'ready', data }))
      .catch((err: unknown) =>
        active &&
        setState({
          status: 'error',
          message: err instanceof Error ? err.message : 'Could not load products.',
        }),
      )
    return () => {
      active = false
    }
  }, [])

  return state
}
