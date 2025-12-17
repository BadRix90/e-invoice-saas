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
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService, Invoice } from '../../../core/services/api';

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
    MatMenuModule,
    MatSnackBarModule
  ],
  templateUrl: './list.html',
  styleUrl: './list.scss'
})
export class ListComponent implements OnInit {
  invoices = signal<Invoice[]>([]);
  isLoading = signal(true);
  displayedColumns = ['invoice_number', 'customer_name', 'invoice_date', 'total', 'status', 'format', 'actions'];

  constructor(
    private apiService: ApiService,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit(): void {
    this.loadInvoices();
  }

  loadInvoices(): void {
    this.isLoading.set(true);
    this.apiService.getInvoices().subscribe({
      next: (data: any) => {
        const invoices = Array.isArray(data) ? data : (data.results || []);
        this.invoices.set(invoices);
        this.isLoading.set(false);
      },
      error: () => {
        this.snackBar.open('Fehler beim Laden der Rechnungen', 'OK', { duration: 3000 });
        this.invoices.set([]);
        this.isLoading.set(false);
      }
    });
  }

  onSearch(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.apiService.getInvoices({ search: value }).subscribe({
      next: (data: any) => {
        const invoices = Array.isArray(data) ? data : (data.results || []);
        this.invoices.set(invoices);
      }
    });
  }

  formatPrice(price: string): string {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(parseFloat(price));
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('de-DE');
  }

  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  deleteInvoice(id: number): void {
    if (confirm('Rechnung wirklich löschen?')) {
      this.apiService.deleteInvoice(id).subscribe({
        next: () => {
          this.invoices.update(list => list.filter(i => i.id !== id));
          this.snackBar.open('Rechnung gelöscht', 'OK', { duration: 2000 });
        },
        error: () => {
          this.snackBar.open('Fehler beim Löschen', 'OK', { duration: 3000 });
        }
      });
    }
  }

  duplicateInvoice(id: number): void {
    this.apiService.duplicateInvoice(id).subscribe({
      next: (newInvoice) => {
        this.invoices.update(list => [newInvoice, ...list]);
        this.snackBar.open('Rechnung dupliziert', 'OK', { duration: 2000 });
      },
      error: () => {
        this.snackBar.open('Fehler beim Duplizieren', 'OK', { duration: 3000 });
      }
    });
  }

  downloadPdf(id: number): void {
    const invoice = this.invoices().find(i => i.id === id);
    if (invoice?.status === 'draft') {
      this.snackBar.open('Bitte Rechnung erst finalisieren', 'OK', { duration: 3000 });
      return;
    }

    this.apiService.downloadInvoicePdf(id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${invoice?.invoice_number || 'rechnung'}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.snackBar.open('PDF heruntergeladen', 'OK', { duration: 2000 });
      },
      error: () => {
        this.snackBar.open('Fehler beim PDF-Download', 'OK', { duration: 3000 });
      }
    });
  }

  downloadXml(id: number): void {
    const invoice = this.invoices().find(i => i.id === id);

    if (invoice?.status === 'draft') {
      this.snackBar.open('Bitte Rechnung erst finalisieren', 'OK', { duration: 3000 });
      return;
    }

    this.apiService.downloadInvoiceXml(id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${invoice?.invoice_number || 'rechnung'}.xml`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.snackBar.open('XML heruntergeladen', 'OK', { duration: 2000 });
      },
      error: (err) => {
        console.error('Download error:', err);
        this.snackBar.open('Fehler beim Download', 'OK', { duration: 3000 });
      }
    });
  }


  finalizeInvoice(id: number): void {
    this.apiService.finalizeInvoice(id).subscribe({
      next: (updated) => {
        this.invoices.update(list => list.map(i => i.id === id ? updated : i));
        this.snackBar.open('Rechnung finalisiert', 'OK', { duration: 2000 });
      },
      error: (err) => {
        const msg = err.error?.error || 'Fehler beim Finalisieren';
        this.snackBar.open(msg, 'OK', { duration: 3000 });
      }
    });
  }

  markSent(id: number): void {
    this.apiService.markInvoiceSent(id).subscribe({
      next: (updated) => {
        this.invoices.update(list => list.map(i => i.id === id ? updated : i));
        this.snackBar.open('Rechnung als versendet markiert', 'OK', { duration: 2000 });
      },
      error: () => {
        this.snackBar.open('Fehler', 'OK', { duration: 3000 });
      }
    });
  }

  markPaid(id: number): void {
    this.apiService.markInvoicePaid(id).subscribe({
      next: (updated) => {
        this.invoices.update(list => list.map(i => i.id === id ? updated : i));
        this.snackBar.open('Rechnung als bezahlt markiert', 'OK', { duration: 2000 });
      },
      error: () => {
        this.snackBar.open('Fehler', 'OK', { duration: 3000 });
      }
    });
  }

  cancelInvoice(id: number): void {
    if (confirm('Rechnung wirklich stornieren?')) {
      this.apiService.cancelInvoice(id).subscribe({
        next: (updated) => {
          this.invoices.update(list => list.map(i => i.id === id ? updated : i));
          this.snackBar.open('Rechnung storniert', 'OK', { duration: 2000 });
        },
        error: () => {
          this.snackBar.open('Fehler beim Stornieren', 'OK', { duration: 3000 });
        }
      });
    }
  }

  sendEmail(id: number): void {
    const invoice = this.invoices().find(i => i.id === id);

    if (invoice?.status === 'draft') {
      this.snackBar.open('Bitte Rechnung erst finalisieren', 'OK', { duration: 3000 });
      return;
    }

    if (!invoice?.customer_name) {
      this.snackBar.open('Kein Kunde zugeordnet', 'OK', { duration: 3000 });
      return;
    }

    const confirmSend = confirm(`Rechnung ${invoice.invoice_number} per E-Mail versenden?`);
    if (!confirmSend) return;

    this.snackBar.open('Sende E-Mail...', '', { duration: 0 });

    this.apiService.sendInvoiceEmail(id).subscribe({
      next: (result) => {
        this.invoices.update(list => list.map(i => i.id === id ? result.invoice : i));
        this.snackBar.open(result.message, 'OK', { duration: 3000 });
      },
      error: (err) => {
        const msg = err.error?.error || 'Fehler beim E-Mail-Versand';
        this.snackBar.open(msg, 'OK', { duration: 3000 });
      }
    });
  }

  validateInvoice(id: number): void {
    this.snackBar.open('Validiere...', '', { duration: 0 });

    this.apiService.validateInvoice(id).subscribe({
      next: (result) => {
        if (result.is_valid) {
          this.snackBar.open('✓ XRechnung ist valide!', 'OK', { duration: 3000 });
        } else {
          const errorMsg = result.errors.length > 0 ? result.errors[0] : 'Validierungsfehler';
          this.snackBar.open(`✗ ${errorMsg}`, 'OK', { duration: 5000 });
        }
      },
      error: () => {
        this.snackBar.open('Fehler bei der Validierung', 'OK', { duration: 3000 });
      }
    });
  }

  exportDatev(): void {
    this.apiService.exportDatev().subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `datev_export_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.snackBar.open('DATEV Export heruntergeladen', 'OK', { duration: 2000 });
      },
      error: () => {
        this.snackBar.open('Fehler beim Export', 'OK', { duration: 3000 });
      }
    });
  }
}
