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
import { MatMenuModule } from '@angular/material/menu';

export interface Invoice {
  id: number;
  invoice_number: string;
  customer_name: string;
  invoice_date: string;
  total: number;
  status: string;
  format: string;
}

@Component({
  selector: 'app-invoice-list',
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
    MatChipsModule,
    MatMenuModule
  ],
  templateUrl: './list.html',
  styleUrl: './list.scss'
})
export class ListComponent implements OnInit {
  invoices = signal<Invoice[]>([]);
  displayedColumns = ['invoice_number', 'customer_name', 'invoice_date', 'total', 'status', 'format', 'actions'];

  statusLabels: Record<string, string> = {
    draft: 'Entwurf',
    final: 'Final',
    sent: 'Versendet',
    paid: 'Bezahlt',
    cancelled: 'Storniert'
  };

  ngOnInit(): void {
    this.loadInvoices();
  }

  private loadInvoices(): void {
    // TODO: API call
    this.invoices.set([
      { id: 1, invoice_number: 'RE-2025-001', customer_name: 'Muster GmbH', invoice_date: '2025-01-15', total: 1428.00, status: 'paid', format: 'zugferd' },
      { id: 2, invoice_number: 'RE-2025-002', customer_name: 'Beispiel AG', invoice_date: '2025-01-18', total: 594.00, status: 'sent', format: 'xrechnung' },
      { id: 3, invoice_number: 'RE-2025-003', customer_name: 'Test KG', invoice_date: '2025-01-20', total: 238.00, status: 'draft', format: 'zugferd' }
    ]);
  }

  formatPrice(price: number): string {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(price);
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('de-DE');
  }

  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  downloadInvoice(id: number, type: 'pdf' | 'xml'): void {
    // TODO: API call
    console.log(`Download ${type} for invoice ${id}`);
  }
}
