import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Customer {
  id: number;
  customer_number: string;
  is_business: boolean;
  company_name: string;
  first_name: string;
  last_name: string;
  display_name: string;
  street: string;
  zip_code: string;
  city: string;
  country: string;
  email: string;
  phone: string;
  vat_id: string;
  leitweg_id: string;
  payment_terms_days: number;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  description: string;
  unit_price: string;
  gross_price: string;
  unit: string;
  vat_rate: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InvoiceItem {
  id: number;
  product: number | null;
  product_name: string;
  position: number;
  sku: string;
  description: string;
  quantity: string;
  unit: string;
  unit_price: string;
  vat_rate: string;
  line_total: string;
  tax_amount: string;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  customer: number;
  customer_name: string;
  status: 'draft' | 'final' | 'sent' | 'paid' | 'cancelled';
  status_display: string;
  format: 'xrechnung' | 'zugferd';
  format_display: string;
  invoice_date: string;
  due_date: string;
  leitweg_id: string;
  buyer_reference: string;
  subtotal: string;
  tax_amount: string;
  total: string;
  notes: string;
  payment_terms: string;
  items: InvoiceItem[];
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly API_URL = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  // ============ CUSTOMERS ============
  getCustomers(params?: { search?: string }): Observable<Customer[]> {
    let httpParams = new HttpParams();
    if (params?.search) {
      httpParams = httpParams.set('search', params.search);
    }
    return this.http.get<Customer[]>(`${this.API_URL}/customers/`, { params: httpParams });
  }

  getCustomer(id: number): Observable<Customer> {
    return this.http.get<Customer>(`${this.API_URL}/customers/${id}/`);
  }

  createCustomer(data: Partial<Customer>): Observable<Customer> {
    return this.http.post<Customer>(`${this.API_URL}/customers/`, data);
  }

  updateCustomer(id: number, data: Partial<Customer>): Observable<Customer> {
    return this.http.patch<Customer>(`${this.API_URL}/customers/${id}/`, data);
  }

  deleteCustomer(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/customers/${id}/`);
  }

  // ============ PRODUCTS ============
  getProducts(params?: { search?: string; is_active?: boolean }): Observable<Product[]> {
    let httpParams = new HttpParams();
    if (params?.search) {
      httpParams = httpParams.set('search', params.search);
    }
    if (params?.is_active !== undefined) {
      httpParams = httpParams.set('is_active', params.is_active.toString());
    }
    return this.http.get<Product[]>(`${this.API_URL}/products/`, { params: httpParams });
  }

  getProduct(id: number): Observable<Product> {
    return this.http.get<Product>(`${this.API_URL}/products/${id}/`);
  }

  createProduct(data: Partial<Product>): Observable<Product> {
    return this.http.post<Product>(`${this.API_URL}/products/`, data);
  }

  updateProduct(id: number, data: Partial<Product>): Observable<Product> {
    return this.http.patch<Product>(`${this.API_URL}/products/${id}/`, data);
  }

  deleteProduct(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/products/${id}/`);
  }

  // ============ INVOICES ============
  getInvoices(params?: { search?: string; status?: string }): Observable<Invoice[]> {
    let httpParams = new HttpParams();
    if (params?.search) {
      httpParams = httpParams.set('search', params.search);
    }
    if (params?.status) {
      httpParams = httpParams.set('status', params.status);
    }
    return this.http.get<Invoice[]>(`${this.API_URL}/invoices/`, { params: httpParams });
  }

  getInvoice(id: number): Observable<Invoice> {
    return this.http.get<Invoice>(`${this.API_URL}/invoices/${id}/`);
  }

  createInvoice(data: Partial<Invoice>): Observable<Invoice> {
    return this.http.post<Invoice>(`${this.API_URL}/invoices/`, data);
  }

  updateInvoice(id: number, data: Partial<Invoice>): Observable<Invoice> {
    return this.http.patch<Invoice>(`${this.API_URL}/invoices/${id}/`, data);
  }

  deleteInvoice(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/invoices/${id}/`);
  }

  // Invoice Actions
  finalizeInvoice(id: number): Observable<Invoice> {
    return this.http.post<Invoice>(`${this.API_URL}/invoices/${id}/finalize/`, {});
  }

  markInvoiceSent(id: number): Observable<Invoice> {
    return this.http.post<Invoice>(`${this.API_URL}/invoices/${id}/mark_sent/`, {});
  }

  markInvoicePaid(id: number): Observable<Invoice> {
    return this.http.post<Invoice>(`${this.API_URL}/invoices/${id}/mark_paid/`, {});
  }

  cancelInvoice(id: number): Observable<Invoice> {
    return this.http.post<Invoice>(`${this.API_URL}/invoices/${id}/cancel/`, {});
  }

  duplicateInvoice(id: number): Observable<Invoice> {
    return this.http.post<Invoice>(`${this.API_URL}/invoices/${id}/duplicate/`, {});
  }

  // ============ INVOICE ITEMS ============
  createInvoiceItem(data: Partial<InvoiceItem> & { invoice: number }): Observable<InvoiceItem> {
    return this.http.post<InvoiceItem>(`${this.API_URL}/invoices/items/`, data);
  }

  updateInvoiceItem(id: number, data: Partial<InvoiceItem>): Observable<InvoiceItem> {
    return this.http.patch<InvoiceItem>(`${this.API_URL}/invoices/items/${id}/`, data);
  }

  deleteInvoiceItem(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/invoices/items/${id}/`);
  }
}
