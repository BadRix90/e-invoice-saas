import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatChipsModule } from '@angular/material/chips';

export interface Product {
  id: number;
  sku: string;
  name: string;
  unit_price: number;
  unit: string;
  vat_rate: number;
  is_active: boolean;
}

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatTableModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatChipsModule
  ],
  templateUrl: './list.html',
  styleUrl: './list.scss'
})
export class ListComponent implements OnInit {
  products = signal<Product[]>([]);
  displayedColumns = ['sku', 'name', 'unit_price', 'vat_rate', 'status', 'actions'];

  ngOnInit(): void {
    this.loadProducts();
  }

  private loadProducts(): void {
    // TODO: API call
    this.products.set([
      { id: 1, sku: 'ART-001', name: 'Beratungsstunde', unit_price: 120.00, unit: 'HUR', vat_rate: 19, is_active: true },
      { id: 2, sku: 'ART-002', name: 'Softwarelizenz', unit_price: 499.00, unit: 'H87', vat_rate: 19, is_active: true },
      { id: 3, sku: 'ART-003', name: 'Support-Paket', unit_price: 89.00, unit: 'MON', vat_rate: 19, is_active: false }
    ]);
  }

  deleteProduct(id: number): void {
    this.products.update(list => list.filter(p => p.id !== id));
  }

  formatPrice(price: number): string {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(price);
  }
}
