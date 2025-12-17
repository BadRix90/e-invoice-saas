import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';

export interface Customer {
  id: number;
  customer_number: string;
  company_name: string;
  city: string;
  email: string;
  leitweg_id: string;
}

@Component({
  selector: 'app-customer-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatTableModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule
  ],
  templateUrl: './list.html',
  styleUrl: './list.scss'
})
export class ListComponent implements OnInit {
  customers = signal<Customer[]>([]);
  displayedColumns = ['customer_number', 'company_name', 'city', 'email', 'actions'];

  ngOnInit(): void {
    this.loadCustomers();
  }

  private loadCustomers(): void {
    // TODO: API call
    this.customers.set([
      { id: 1, customer_number: 'K-001', company_name: 'Muster GmbH', city: 'Berlin', email: 'info@muster.de', leitweg_id: '' },
      { id: 2, customer_number: 'K-002', company_name: 'Beispiel AG', city: 'München', email: 'kontakt@beispiel.de', leitweg_id: '991-12345-67' }
    ]);
  }

  deleteCustomer(id: number): void {
    // TODO: API call + confirm dialog
    this.customers.update(list => list.filter(c => c.id !== id));
  }
}
