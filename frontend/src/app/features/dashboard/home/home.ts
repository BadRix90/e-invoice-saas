import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { ApiService } from '../../../core/services/api';

interface StatCard {
  title: string;
  value: number;
  icon: string;
  color: string;
  route: string;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatCardModule,
    MatIconModule,
    MatButtonModule
  ],
  templateUrl: './home.html',
  styleUrl: './home.scss'
})
export class HomeComponent implements OnInit {
  stats = signal<StatCard[]>([
    { title: 'Rechnungen', value: 0, icon: 'receipt_long', color: '#1976d2', route: '/dashboard/invoices' },
    { title: 'Offen', value: 0, icon: 'pending', color: '#f57c00', route: '/dashboard/invoices' },
    { title: 'Kunden', value: 0, icon: 'people', color: '#388e3c', route: '/dashboard/customers' },
    { title: 'Produkte', value: 0, icon: 'inventory_2', color: '#7b1fa2', route: '/dashboard/products' }
  ]);

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadStats();
  }

  private loadStats(): void {
    // Kunden zählen
    this.apiService.getCustomers().subscribe({
      next: (customers) => {
        this.stats.update(stats => stats.map(s =>
          s.title === 'Kunden' ? { ...s, value: customers.length } : s
        ));
      }
    });

    // Produkte zählen
    this.apiService.getProducts().subscribe({
      next: (products) => {
        this.stats.update(stats => stats.map(s =>
          s.title === 'Produkte' ? { ...s, value: products.length } : s
        ));
      }
    });

    // Rechnungen zählen
    this.apiService.getInvoices().subscribe({
      next: (invoices) => {
        const total = invoices.length;
        const open = invoices.filter(i => i.status === 'sent' || i.status === 'final').length;
        this.stats.update(stats => stats.map(s => {
          if (s.title === 'Rechnungen') return { ...s, value: total };
          if (s.title === 'Offen') return { ...s, value: open };
          return s;
        }));
      }
    });
  }
}
