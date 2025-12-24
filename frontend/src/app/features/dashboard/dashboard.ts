import { Component, OnInit, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive, Router, NavigationEnd } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { AuthService } from '../../core/services/auth';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatMenuModule
  ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class DashboardComponent implements OnInit, OnDestroy {
  // Alle Menu-Items (für Desktop Sidenav)
  menuItems = [
    { icon: 'dashboard', label: 'Übersicht', route: '/dashboard' },
    { icon: 'receipt_long', label: 'Rechnungen', route: '/dashboard/invoices' },
    { icon: 'people', label: 'Kunden', route: '/dashboard/customers' },
    { icon: 'inventory_2', label: 'Produkte', route: '/dashboard/products' },
    { icon: 'groups', label: 'Team', route: '/dashboard/team' },
    { icon: 'settings', label: 'Einstellungen', route: '/dashboard/settings' }
  ];

  // Nur Hauptnavigation (für Mobile Bottom Nav)
  bottomNavItems = [
    { icon: 'dashboard', label: 'Übersicht', route: '/dashboard' },
    { icon: 'receipt_long', label: 'Rechnungen', route: '/dashboard/invoices' },
    { icon: 'people', label: 'Kunden', route: '/dashboard/customers' },
    { icon: 'inventory_2', label: 'Produkte', route: '/dashboard/products' }
  ];

  isMobile = false;
  currentPageTitle = '';
  private routerSub!: Subscription;
  private readonly BREAKPOINT = 768;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.checkScreenSize();
    this.updatePageTitle(this.router.url);

    this.routerSub = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        this.updatePageTitle(event.urlAfterRedirects);
      });
  }

  ngOnDestroy(): void {
    this.routerSub?.unsubscribe();
  }

  @HostListener('window:resize')
  onResize(): void {
    this.checkScreenSize();
  }

  private checkScreenSize(): void {
    this.isMobile = window.innerWidth < this.BREAKPOINT;
  }

  private updatePageTitle(url: string): void {
    const allItems = [...this.menuItems];
    const item = allItems.find(i => url.startsWith(i.route) && i.route !== '/dashboard')
               || allItems.find(i => i.route === '/dashboard');
    this.currentPageTitle = item?.label || 'Dashboard';
  }

  logout(): void {
    this.authService.logout();
  }
}
