import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

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

  recentInvoices = signal<any[]>([]);

  ngOnInit(): void {
    // TODO: Load stats from API
    this.loadStats();
  }

  private loadStats(): void {
    // Placeholder - wird später mit echten API-Daten ersetzt
    this.stats.set([
      { title: 'Rechnungen', value: 24, icon: 'receipt_long', color: '#1976d2', route: '/dashboard/invoices' },
      { title: 'Offen', value: 5, icon: 'pending', color: '#f57c00', route: '/dashboard/invoices' },
      { title: 'Kunden', value: 12, icon: 'people', color: '#388e3c', route: '/dashboard/customers' },
      { title: 'Produkte', value: 48, icon: 'inventory_2', color: '#7b1fa2', route: '/dashboard/products' }
    ]);
  }
}
