import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth-guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full'
  },
  {
    path: 'auth/login',
    loadComponent: () => import('./features/auth/login/login').then(m => m.LoginComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard').then(m => m.DashboardComponent),
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./features/dashboard/home/home').then(m => m.HomeComponent)
      },
      {
        path: 'customers',
        loadComponent: () => import('./features/customers/list/list').then(m => m.ListComponent)
      },
      {
        path: 'customers/new',
        loadComponent: () => import('./features/customers/form/form').then(m => m.FormComponent)
      },
      {
        path: 'customers/:id',
        loadComponent: () => import('./features/customers/form/form').then(m => m.FormComponent)
      },
      {
        path: 'products',
        loadComponent: () => import('./features/products/list/list').then(m => m.ListComponent)
      },
      {
        path: 'products/new',
        loadComponent: () => import('./features/products/form/form').then(m => m.FormComponent)
      },
      {
        path: 'products/:id',
        loadComponent: () => import('./features/products/form/form').then(m => m.FormComponent)
      },
      {
        path: 'invoices',
        loadComponent: () => import('./features/invoices/list/list').then(m => m.ListComponent)
      },
      {
        path: 'invoices/new',
        loadComponent: () => import('./features/invoices/form/form').then(m => m.FormComponent)
      },
      {
        path: 'invoices/:id',
        loadComponent: () => import('./features/invoices/form/form').then(m => m.FormComponent)
      },
    ]
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];
